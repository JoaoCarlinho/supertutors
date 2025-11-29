"""Redis Service - Centralized Redis connection and caching operations (Story 8-3).

Implements:
- AC-1: Redis client connection with graceful fallback
- AC-2: Singleton pattern with connection pooling
- AC-3: OCR cache layer with image hash keys
- AC-4: Cache key strategy with subject parameter
- AC-5: Cache invalidation methods
- AC-6: Celebration cooldown storage
- AC-7: Cache hit/miss logging for monitoring
"""
import os
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Try to import redis, but allow graceful fallback
try:
    import redis
    from redis.connection import ConnectionPool
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis package not installed. Caching will be disabled.")


class RedisService:
    """Singleton Redis service for OCR caching and celebration cooldowns.

    Provides:
    - Connection pooling for efficient Redis connections
    - OCR result caching with configurable TTL
    - Celebration cooldown tracking
    - Cache hit/miss logging for monitoring
    """

    _instance: Optional['RedisService'] = None
    _initialized: bool = False

    # Default TTLs (in seconds)
    OCR_CACHE_TTL = 86400  # 24 hours (AC-3)
    CELEBRATION_COOLDOWN_TTL = 120  # 2 minutes (AC-6)

    def __new__(cls) -> 'RedisService':
        """Singleton pattern - only one Redis connection per process (AC-2)."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize Redis connection with pooling."""
        if self._initialized:
            return

        self.client: Optional[Any] = None
        self._connected: bool = False

        if not REDIS_AVAILABLE:
            logger.warning("Redis not available - caching disabled")
            self._initialized = True
            return

        self._init_client()
        self._initialized = True

    def _init_client(self) -> None:
        """Initialize Redis client with connection pooling (AC-2).

        Uses REDIS_URL environment variable for connection string.
        Supports both local Redis and AWS ElastiCache.
        """
        redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')

        try:
            # Create connection pool for efficient connection reuse (AC-2)
            pool = ConnectionPool.from_url(
                redis_url,
                decode_responses=True,
                max_connections=10
            )
            self.client = redis.Redis(connection_pool=pool)

            # Test connection
            self.client.ping()
            self._connected = True
            logger.info(f"Redis connected successfully to {redis_url.split('@')[-1]}")

        except Exception as e:
            self._connected = False
            logger.error(f"Failed to connect to Redis: {e}")
            logger.warning("OCR caching disabled - falling back to non-cached mode")

    def is_connected(self) -> bool:
        """Check if Redis connection is active."""
        return self._connected and self.client is not None

    def health_check(self) -> Dict[str, Any]:
        """Health check for Redis connection (AC-2).

        Returns:
            Dictionary with connection status and metrics
        """
        if not self.is_connected():
            return {
                'status': 'disconnected',
                'redis_available': REDIS_AVAILABLE,
                'error': 'Not connected to Redis'
            }

        try:
            self.client.ping()
            info = self.client.info(section='stats')

            return {
                'status': 'connected',
                'redis_available': True,
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0),
                'connected_clients': info.get('connected_clients', 0)
            }
        except Exception as e:
            return {
                'status': 'error',
                'redis_available': REDIS_AVAILABLE,
                'error': str(e)
            }

    # ========== OCR Caching Methods (AC-3, AC-4) ==========

    def _get_ocr_cache_key(self, image_hash: str, subject: Optional[str] = None) -> str:
        """Generate cache key for OCR results (AC-4).

        Key format: ocr:{image_hash}:{subject}
        Subject is included because different prompts produce different results.
        """
        subject_key = subject.lower() if subject else 'none'
        return f"ocr:{image_hash}:{subject_key}"

    def get_cached_ocr(self, image_hash: str, subject: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Retrieve cached OCR result (AC-3).

        Args:
            image_hash: MD5 hash of image content
            subject: Subject hint used for OCR (affects prompt)

        Returns:
            Cached OCR result dict or None if not found/cache disabled
        """
        if not self.is_connected():
            logger.debug("Redis not connected - cache miss (disabled)")
            return None

        key = self._get_ocr_cache_key(image_hash, subject)

        try:
            cached = self.client.get(key)

            if cached:
                logger.info(f"OCR cache HIT for {key}")
                result = json.loads(cached)
                result['cached'] = True
                result['cache_timestamp'] = result.get('_cached_at', '')
                return result
            else:
                logger.info(f"OCR cache MISS for {key}")
                return None

        except Exception as e:
            logger.error(f"Error retrieving OCR cache: {e}")
            return None

    def cache_ocr_result(
        self,
        image_hash: str,
        result: Dict[str, Any],
        subject: Optional[str] = None,
        ttl: Optional[int] = None
    ) -> bool:
        """Cache OCR result (AC-3).

        Args:
            image_hash: MD5 hash of image content
            result: OCR result dictionary to cache
            subject: Subject hint used for OCR
            ttl: Time-to-live in seconds (default: 24 hours)

        Returns:
            True if cached successfully, False otherwise
        """
        if not self.is_connected():
            logger.debug("Redis not connected - skipping cache")
            return False

        key = self._get_ocr_cache_key(image_hash, subject)
        ttl = ttl or self.OCR_CACHE_TTL

        try:
            # Add caching metadata
            result_to_cache = result.copy()
            result_to_cache['_cached_at'] = datetime.now().isoformat()
            result_to_cache['_image_hash'] = image_hash
            result_to_cache['_subject'] = subject

            self.client.setex(key, ttl, json.dumps(result_to_cache))
            logger.info(f"OCR result cached at {key} (TTL: {ttl}s)")
            return True

        except Exception as e:
            logger.error(f"Error caching OCR result: {e}")
            return False

    def invalidate_ocr_cache(self, image_hash: str) -> int:
        """Invalidate all OCR cache entries for an image (AC-5).

        Removes all cached results for the given image hash,
        regardless of subject hint.

        Args:
            image_hash: MD5 hash of image content

        Returns:
            Number of keys deleted
        """
        if not self.is_connected():
            return 0

        try:
            pattern = f"ocr:{image_hash}:*"
            keys = list(self.client.scan_iter(match=pattern))

            if keys:
                deleted = self.client.delete(*keys)
                logger.info(f"Invalidated {deleted} cache entries for image {image_hash}")
                return deleted

            logger.info(f"No cache entries found for image {image_hash}")
            return 0

        except Exception as e:
            logger.error(f"Error invalidating OCR cache: {e}")
            return 0

    # ========== Celebration Cooldown Methods (AC-6) ==========

    def _get_celebration_key(self, conversation_id: str) -> str:
        """Generate cache key for celebration cooldown (AC-6)."""
        return f"celebration:{conversation_id}"

    def is_celebration_on_cooldown(self, conversation_id: str) -> bool:
        """Check if celebration is on cooldown (AC-6).

        Args:
            conversation_id: Conversation UUID

        Returns:
            True if cooldown is active, False otherwise
        """
        if not self.is_connected():
            # Fallback: no cooldown check without Redis
            return False

        key = self._get_celebration_key(conversation_id)

        try:
            return self.client.exists(key) > 0
        except Exception as e:
            logger.error(f"Error checking celebration cooldown: {e}")
            return False

    def set_celebration_cooldown(self, conversation_id: str, ttl: Optional[int] = None) -> bool:
        """Set celebration cooldown (AC-6).

        Args:
            conversation_id: Conversation UUID
            ttl: Cooldown duration in seconds (default: 2 minutes)

        Returns:
            True if set successfully, False otherwise
        """
        if not self.is_connected():
            return False

        key = self._get_celebration_key(conversation_id)
        ttl = ttl or self.CELEBRATION_COOLDOWN_TTL

        try:
            self.client.setex(key, ttl, datetime.now().isoformat())
            logger.debug(f"Celebration cooldown set for {conversation_id} ({ttl}s)")
            return True
        except Exception as e:
            logger.error(f"Error setting celebration cooldown: {e}")
            return False

    def clear_celebration_cooldown(self, conversation_id: str) -> bool:
        """Clear celebration cooldown (AC-6).

        Args:
            conversation_id: Conversation UUID

        Returns:
            True if cleared successfully, False otherwise
        """
        if not self.is_connected():
            return False

        key = self._get_celebration_key(conversation_id)

        try:
            self.client.delete(key)
            logger.debug(f"Celebration cooldown cleared for {conversation_id}")
            return True
        except Exception as e:
            logger.error(f"Error clearing celebration cooldown: {e}")
            return False

    def get_celebration_cooldown_remaining(self, conversation_id: str) -> Optional[int]:
        """Get remaining cooldown time in seconds (AC-6).

        Args:
            conversation_id: Conversation UUID

        Returns:
            Remaining seconds or None if no cooldown
        """
        if not self.is_connected():
            return None

        key = self._get_celebration_key(conversation_id)

        try:
            ttl = self.client.ttl(key)
            return ttl if ttl > 0 else None
        except Exception as e:
            logger.error(f"Error getting celebration cooldown TTL: {e}")
            return None

    # ========== Monitoring Methods (AC-7) ==========

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics for monitoring (AC-7).

        Returns:
            Dictionary with cache metrics
        """
        if not self.is_connected():
            return {
                'status': 'disabled',
                'ocr_cache_count': 0,
                'celebration_cooldown_count': 0
            }

        try:
            # Count OCR cache keys
            ocr_keys = list(self.client.scan_iter(match='ocr:*'))

            # Count celebration cooldown keys
            celebration_keys = list(self.client.scan_iter(match='celebration:*'))

            # Get Redis info
            info = self.client.info(section='memory')

            return {
                'status': 'active',
                'ocr_cache_count': len(ocr_keys),
                'celebration_cooldown_count': len(celebration_keys),
                'used_memory': info.get('used_memory_human', 'unknown'),
                'used_memory_peak': info.get('used_memory_peak_human', 'unknown')
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }


# Global singleton instance
_redis_service: Optional[RedisService] = None


def get_redis_service() -> RedisService:
    """Get or create the singleton RedisService instance.

    Returns:
        RedisService singleton instance
    """
    global _redis_service
    if _redis_service is None:
        _redis_service = RedisService()
    return _redis_service
