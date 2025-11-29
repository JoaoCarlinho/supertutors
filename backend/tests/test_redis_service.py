"""Unit tests for Redis Service (Story 8-3).

Tests for:
- AC-1: Redis client installation and connection
- AC-2: Singleton pattern and connection pooling
- AC-3: OCR cache layer with image hash keys
- AC-4: Cache key strategy with subject parameter
- AC-5: Cache invalidation
- AC-6: Celebration cooldown storage
- AC-7: Cache hit/miss logging
"""
import pytest
import json
from unittest.mock import Mock, patch, MagicMock


def reset_redis_singleton():
    """Reset the Redis singleton for test isolation."""
    import app.services.redis_service as redis_module
    redis_module.RedisService._instance = None
    redis_module.RedisService._initialized = False
    redis_module._redis_service = None


class TestRedisServiceSingleton:
    """Test suite for singleton pattern (AC-2)."""

    def test_singleton_pattern(self):
        """AC-2: RedisService uses singleton pattern."""
        with patch.dict('os.environ', {'REDIS_URL': 'redis://localhost:6379/0'}):
            with patch('app.services.redis_service.REDIS_AVAILABLE', True):
                with patch('app.services.redis_service.redis') as mock_redis:
                    mock_client = MagicMock()
                    mock_redis.Redis.return_value = mock_client
                    mock_redis.connection.ConnectionPool.from_url.return_value = MagicMock()
                    mock_client.ping.return_value = True

                    import app.services.redis_service as redis_module
                    reset_redis_singleton()

                    # Get two instances
                    service1 = redis_module.RedisService()
                    service2 = redis_module.RedisService()

                    # Should be the same instance
                    assert service1 is service2

    def test_get_redis_service_helper(self):
        """AC-2: get_redis_service() returns singleton."""
        with patch.dict('os.environ', {'REDIS_URL': 'redis://localhost:6379/0'}):
            with patch('app.services.redis_service.REDIS_AVAILABLE', True):
                with patch('app.services.redis_service.redis') as mock_redis:
                    mock_client = MagicMock()
                    mock_redis.Redis.return_value = mock_client
                    mock_redis.connection.ConnectionPool.from_url.return_value = MagicMock()
                    mock_client.ping.return_value = True

                    import app.services.redis_service as redis_module
                    reset_redis_singleton()

                    service1 = redis_module.get_redis_service()
                    service2 = redis_module.get_redis_service()

                    assert service1 is service2


class TestRedisServiceConnection:
    """Test suite for connection handling (AC-1)."""

    def test_connection_success(self):
        """AC-1: Service connects successfully to Redis."""
        with patch.dict('os.environ', {'REDIS_URL': 'redis://localhost:6379/0'}):
            with patch('app.services.redis_service.REDIS_AVAILABLE', True):
                with patch('app.services.redis_service.redis') as mock_redis:
                    mock_client = MagicMock()
                    mock_redis.Redis.return_value = mock_client
                    mock_redis.connection.ConnectionPool.from_url.return_value = MagicMock()
                    mock_client.ping.return_value = True

                    import app.services.redis_service as redis_module
                    reset_redis_singleton()

                    service = redis_module.RedisService()

                    assert service._connected is True
                    assert service.is_connected() is True

    def test_connection_failure_graceful(self):
        """AC-1: Service handles connection failures gracefully."""
        with patch.dict('os.environ', {'REDIS_URL': 'redis://localhost:6379/0'}):
            with patch('app.services.redis_service.REDIS_AVAILABLE', True):
                with patch('app.services.redis_service.redis') as mock_redis:
                    mock_client = MagicMock()
                    mock_redis.Redis.return_value = mock_client
                    mock_redis.connection.ConnectionPool.from_url.return_value = MagicMock()
                    # Make ping fail to simulate connection failure
                    mock_client.ping.side_effect = Exception("Connection refused")

                    import app.services.redis_service as redis_module
                    reset_redis_singleton()

                    service = redis_module.RedisService()

                    # Should not raise, should gracefully handle
                    assert service._connected is False

    def test_health_check_connected(self):
        """AC-2: Health check returns connection status when connected."""
        with patch.dict('os.environ', {'REDIS_URL': 'redis://localhost:6379/0'}):
            with patch('app.services.redis_service.REDIS_AVAILABLE', True):
                with patch('app.services.redis_service.redis') as mock_redis:
                    mock_client = MagicMock()
                    mock_redis.Redis.return_value = mock_client
                    mock_redis.connection.ConnectionPool.from_url.return_value = MagicMock()
                    mock_client.ping.return_value = True
                    mock_client.info.return_value = {
                        'keyspace_hits': 100,
                        'keyspace_misses': 10,
                        'connected_clients': 5
                    }

                    import app.services.redis_service as redis_module
                    reset_redis_singleton()

                    service = redis_module.RedisService()
                    health = service.health_check()

                    assert health['status'] == 'connected'
                    assert health['keyspace_hits'] == 100

    def test_health_check_disconnected(self):
        """AC-2: Health check returns disconnected status."""
        with patch('app.services.redis_service.REDIS_AVAILABLE', False):
            import app.services.redis_service as redis_module
            reset_redis_singleton()

            service = redis_module.RedisService()
            health = service.health_check()

            assert health['status'] == 'disconnected'


class TestOCRCaching:
    """Test suite for OCR caching (AC-3, AC-4)."""

    def test_cache_key_format(self):
        """AC-4: Cache key includes image hash and subject."""
        with patch('app.services.redis_service.REDIS_AVAILABLE', False):
            import app.services.redis_service as redis_module
            reset_redis_singleton()

            service = redis_module.RedisService()
            key = service._get_ocr_cache_key('abc12345', 'algebra')

            assert key == 'ocr:abc12345:algebra'

    def test_cache_key_without_subject(self):
        """AC-4: Cache key handles missing subject."""
        with patch('app.services.redis_service.REDIS_AVAILABLE', False):
            import app.services.redis_service as redis_module
            reset_redis_singleton()

            service = redis_module.RedisService()
            key = service._get_ocr_cache_key('abc12345', None)

            assert key == 'ocr:abc12345:none'

    def test_cache_hit(self):
        """AC-3: Cache returns stored result on hit."""
        with patch.dict('os.environ', {'REDIS_URL': 'redis://localhost:6379/0'}):
            with patch('app.services.redis_service.REDIS_AVAILABLE', True):
                with patch('app.services.redis_service.redis') as mock_redis:
                    mock_client = MagicMock()
                    mock_redis.Redis.return_value = mock_client
                    mock_redis.connection.ConnectionPool.from_url.return_value = MagicMock()
                    mock_client.ping.return_value = True

                    cached_data = {
                        'success': True,
                        'extracted_text': 'x + 5 = 10',
                        'confidence': 0.92
                    }
                    mock_client.get.return_value = json.dumps(cached_data)

                    import app.services.redis_service as redis_module
                    reset_redis_singleton()

                    service = redis_module.RedisService()
                    result = service.get_cached_ocr('abc12345', 'algebra')

                    assert result is not None
                    assert result['extracted_text'] == 'x + 5 = 10'
                    assert result['cached'] is True

    def test_cache_miss(self):
        """AC-3: Cache returns None on miss."""
        with patch.dict('os.environ', {'REDIS_URL': 'redis://localhost:6379/0'}):
            with patch('app.services.redis_service.REDIS_AVAILABLE', True):
                with patch('app.services.redis_service.redis') as mock_redis:
                    mock_client = MagicMock()
                    mock_redis.Redis.return_value = mock_client
                    mock_redis.connection.ConnectionPool.from_url.return_value = MagicMock()
                    mock_client.ping.return_value = True
                    mock_client.get.return_value = None

                    import app.services.redis_service as redis_module
                    reset_redis_singleton()

                    service = redis_module.RedisService()
                    result = service.get_cached_ocr('abc12345', 'algebra')

                    assert result is None

    def test_cache_ocr_result(self):
        """AC-3: OCR result is cached with TTL."""
        with patch.dict('os.environ', {'REDIS_URL': 'redis://localhost:6379/0'}):
            with patch('app.services.redis_service.REDIS_AVAILABLE', True):
                with patch('app.services.redis_service.redis') as mock_redis:
                    mock_client = MagicMock()
                    mock_redis.Redis.return_value = mock_client
                    mock_redis.connection.ConnectionPool.from_url.return_value = MagicMock()
                    mock_client.ping.return_value = True

                    import app.services.redis_service as redis_module
                    reset_redis_singleton()

                    service = redis_module.RedisService()
                    result = {
                        'success': True,
                        'extracted_text': 'x + 5 = 10',
                        'confidence': 0.92
                    }

                    success = service.cache_ocr_result('abc12345', result, 'algebra')

                    assert success is True
                    mock_client.setex.assert_called_once()
                    # Check TTL is 24 hours (86400 seconds)
                    call_args = mock_client.setex.call_args
                    assert call_args[0][1] == 86400  # TTL

    def test_cache_with_custom_ttl(self):
        """AC-3: Cache accepts custom TTL."""
        with patch.dict('os.environ', {'REDIS_URL': 'redis://localhost:6379/0'}):
            with patch('app.services.redis_service.REDIS_AVAILABLE', True):
                with patch('app.services.redis_service.redis') as mock_redis:
                    mock_client = MagicMock()
                    mock_redis.Redis.return_value = mock_client
                    mock_redis.connection.ConnectionPool.from_url.return_value = MagicMock()
                    mock_client.ping.return_value = True

                    import app.services.redis_service as redis_module
                    reset_redis_singleton()

                    service = redis_module.RedisService()
                    result = {'success': True, 'extracted_text': 'test'}

                    service.cache_ocr_result('abc12345', result, ttl=3600)

                    call_args = mock_client.setex.call_args
                    assert call_args[0][1] == 3600  # Custom TTL


class TestCacheInvalidation:
    """Test suite for cache invalidation (AC-5)."""

    def test_invalidate_all_subjects(self):
        """AC-5: Invalidation removes all subject variants."""
        with patch.dict('os.environ', {'REDIS_URL': 'redis://localhost:6379/0'}):
            with patch('app.services.redis_service.REDIS_AVAILABLE', True):
                with patch('app.services.redis_service.redis') as mock_redis:
                    mock_client = MagicMock()
                    mock_redis.Redis.return_value = mock_client
                    mock_redis.connection.ConnectionPool.from_url.return_value = MagicMock()
                    mock_client.ping.return_value = True

                    # Mock scan_iter to return multiple keys
                    mock_client.scan_iter.return_value = iter([
                        'ocr:abc12345:algebra',
                        'ocr:abc12345:geometry',
                        'ocr:abc12345:none'
                    ])
                    mock_client.delete.return_value = 3

                    import app.services.redis_service as redis_module
                    reset_redis_singleton()

                    service = redis_module.RedisService()
                    deleted = service.invalidate_ocr_cache('abc12345')

                    assert deleted == 3

    def test_invalidate_no_keys(self):
        """AC-5: Invalidation handles no matching keys."""
        with patch.dict('os.environ', {'REDIS_URL': 'redis://localhost:6379/0'}):
            with patch('app.services.redis_service.REDIS_AVAILABLE', True):
                with patch('app.services.redis_service.redis') as mock_redis:
                    mock_client = MagicMock()
                    mock_redis.Redis.return_value = mock_client
                    mock_redis.connection.ConnectionPool.from_url.return_value = MagicMock()
                    mock_client.ping.return_value = True
                    mock_client.scan_iter.return_value = iter([])

                    import app.services.redis_service as redis_module
                    reset_redis_singleton()

                    service = redis_module.RedisService()
                    deleted = service.invalidate_ocr_cache('notfound')

                    assert deleted == 0


class TestCelebrationCooldowns:
    """Test suite for celebration cooldown storage (AC-6)."""

    def test_celebration_key_format(self):
        """AC-6: Celebration key format is correct."""
        with patch('app.services.redis_service.REDIS_AVAILABLE', False):
            import app.services.redis_service as redis_module
            reset_redis_singleton()

            service = redis_module.RedisService()
            key = service._get_celebration_key('conv-123')

            assert key == 'celebration:conv-123'

    def test_set_celebration_cooldown(self):
        """AC-6: Cooldown is set with 2-minute TTL."""
        with patch.dict('os.environ', {'REDIS_URL': 'redis://localhost:6379/0'}):
            with patch('app.services.redis_service.REDIS_AVAILABLE', True):
                with patch('app.services.redis_service.redis') as mock_redis:
                    mock_client = MagicMock()
                    mock_redis.Redis.return_value = mock_client
                    mock_redis.connection.ConnectionPool.from_url.return_value = MagicMock()
                    mock_client.ping.return_value = True

                    import app.services.redis_service as redis_module
                    reset_redis_singleton()

                    service = redis_module.RedisService()
                    result = service.set_celebration_cooldown('conv-123')

                    assert result is True
                    mock_client.setex.assert_called_once()
                    # Check TTL is 2 minutes (120 seconds)
                    call_args = mock_client.setex.call_args
                    assert call_args[0][1] == 120

    def test_check_cooldown_active(self):
        """AC-6: Check cooldown returns True when active."""
        with patch.dict('os.environ', {'REDIS_URL': 'redis://localhost:6379/0'}):
            with patch('app.services.redis_service.REDIS_AVAILABLE', True):
                with patch('app.services.redis_service.redis') as mock_redis:
                    mock_client = MagicMock()
                    mock_redis.Redis.return_value = mock_client
                    mock_redis.connection.ConnectionPool.from_url.return_value = MagicMock()
                    mock_client.ping.return_value = True
                    mock_client.exists.return_value = 1

                    import app.services.redis_service as redis_module
                    reset_redis_singleton()

                    service = redis_module.RedisService()
                    on_cooldown = service.is_celebration_on_cooldown('conv-123')

                    assert on_cooldown is True

    def test_check_cooldown_inactive(self):
        """AC-6: Check cooldown returns False when not active."""
        with patch.dict('os.environ', {'REDIS_URL': 'redis://localhost:6379/0'}):
            with patch('app.services.redis_service.REDIS_AVAILABLE', True):
                with patch('app.services.redis_service.redis') as mock_redis:
                    mock_client = MagicMock()
                    mock_redis.Redis.return_value = mock_client
                    mock_redis.connection.ConnectionPool.from_url.return_value = MagicMock()
                    mock_client.ping.return_value = True
                    mock_client.exists.return_value = 0

                    import app.services.redis_service as redis_module
                    reset_redis_singleton()

                    service = redis_module.RedisService()
                    on_cooldown = service.is_celebration_on_cooldown('conv-123')

                    assert on_cooldown is False

    def test_clear_cooldown(self):
        """AC-6: Cooldown can be cleared manually."""
        with patch.dict('os.environ', {'REDIS_URL': 'redis://localhost:6379/0'}):
            with patch('app.services.redis_service.REDIS_AVAILABLE', True):
                with patch('app.services.redis_service.redis') as mock_redis:
                    mock_client = MagicMock()
                    mock_redis.Redis.return_value = mock_client
                    mock_redis.connection.ConnectionPool.from_url.return_value = MagicMock()
                    mock_client.ping.return_value = True

                    import app.services.redis_service as redis_module
                    reset_redis_singleton()

                    service = redis_module.RedisService()
                    result = service.clear_celebration_cooldown('conv-123')

                    assert result is True
                    mock_client.delete.assert_called_once()

    def test_get_cooldown_remaining(self):
        """AC-6: Get remaining cooldown time."""
        with patch.dict('os.environ', {'REDIS_URL': 'redis://localhost:6379/0'}):
            with patch('app.services.redis_service.REDIS_AVAILABLE', True):
                with patch('app.services.redis_service.redis') as mock_redis:
                    mock_client = MagicMock()
                    mock_redis.Redis.return_value = mock_client
                    mock_redis.connection.ConnectionPool.from_url.return_value = MagicMock()
                    mock_client.ping.return_value = True
                    mock_client.ttl.return_value = 90  # 90 seconds remaining

                    import app.services.redis_service as redis_module
                    reset_redis_singleton()

                    service = redis_module.RedisService()
                    remaining = service.get_celebration_cooldown_remaining('conv-123')

                    assert remaining == 90


class TestCacheStats:
    """Test suite for cache statistics (AC-7)."""

    def test_get_cache_stats(self):
        """AC-7: Cache stats includes OCR and celebration counts."""
        with patch.dict('os.environ', {'REDIS_URL': 'redis://localhost:6379/0'}):
            with patch('app.services.redis_service.REDIS_AVAILABLE', True):
                with patch('app.services.redis_service.redis') as mock_redis:
                    mock_client = MagicMock()
                    mock_redis.Redis.return_value = mock_client
                    mock_redis.connection.ConnectionPool.from_url.return_value = MagicMock()
                    mock_client.ping.return_value = True

                    # Mock scan_iter for counting keys
                    mock_client.scan_iter.side_effect = [
                        iter(['ocr:abc:algebra', 'ocr:def:geometry']),  # OCR keys
                        iter(['celebration:conv-1'])  # Celebration keys
                    ]
                    mock_client.info.return_value = {
                        'used_memory_human': '1.5M',
                        'used_memory_peak_human': '2.0M'
                    }

                    import app.services.redis_service as redis_module
                    reset_redis_singleton()

                    service = redis_module.RedisService()
                    stats = service.get_cache_stats()

                    assert stats['status'] == 'active'
                    assert stats['ocr_cache_count'] == 2
                    assert stats['celebration_cooldown_count'] == 1


class TestRedisUnavailable:
    """Test suite for Redis unavailable scenarios."""

    def test_service_works_without_redis(self):
        """Service initializes even when redis package unavailable."""
        with patch('app.services.redis_service.REDIS_AVAILABLE', False):
            import app.services.redis_service as redis_module
            reset_redis_singleton()

            service = redis_module.RedisService()

            assert service.is_connected() is False

    def test_cache_operations_return_gracefully(self):
        """Cache operations return gracefully when Redis unavailable."""
        with patch('app.services.redis_service.REDIS_AVAILABLE', False):
            import app.services.redis_service as redis_module
            reset_redis_singleton()

            service = redis_module.RedisService()

            # All operations should return None/False gracefully
            assert service.get_cached_ocr('abc', 'algebra') is None
            assert service.cache_ocr_result('abc', {}) is False
            assert service.invalidate_ocr_cache('abc') == 0
            assert service.is_celebration_on_cooldown('conv') is False
            assert service.set_celebration_cooldown('conv') is False
