"""Celebration Service - manages streak tracking and celebration triggers.

Enhanced with Redis-backed cooldowns (Story 8-3, AC-6):
- Cooldowns persist across server restarts
- TTL: 2 minutes (120 seconds)
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from app.extensions import socketio

# Import Redis service for cooldown persistence (Story 8-3)
try:
    from app.services.redis_service import get_redis_service
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

logger = logging.getLogger(__name__)


class CelebrationService:
    """Service for tracking streaks and triggering celebrations.

    Cooldowns are stored in Redis when available (Story 8-3, AC-6),
    with fallback to in-memory storage.
    """

    def __init__(self):
        """Initialize celebration service."""
        self._in_memory_cooldowns = {}  # Fallback in-memory cooldown tracking
        self._redis_service = None

        # Try to use Redis for cooldowns
        if REDIS_AVAILABLE:
            try:
                self._redis_service = get_redis_service()
                if self._redis_service.is_connected():
                    logger.info("Initialized Celebration service with Redis cooldowns")
                else:
                    logger.info("Initialized Celebration service (Redis not connected, using in-memory)")
            except Exception as e:
                logger.warning(f"Failed to connect Redis for cooldowns: {e}")
                logger.info("Initialized Celebration service with in-memory cooldowns")
        else:
            logger.info("Initialized Celebration service with in-memory cooldowns")

    def update_streak(
        self,
        conversation_id: str,
        is_correct: bool,
        current_streak: int = 0
    ) -> Dict[str, Any]:
        """Update streak and check for celebration trigger.

        Args:
            conversation_id: Conversation UUID
            is_correct: Whether answer was correct
            current_streak: Current streak count

        Returns:
            Dictionary with new_streak and celebration_triggered
        """
        # Update streak
        if is_correct:
            new_streak = current_streak + 1
        else:
            new_streak = 0

        # Check for celebration trigger
        celebration_triggered = False
        if new_streak > 0 and new_streak % 3 == 0:
            celebration_triggered = self._trigger_celebration(conversation_id, new_streak)

        return {
            'new_streak': new_streak,
            'celebration_triggered': celebration_triggered
        }

    def _trigger_celebration(self, conversation_id: str, streak: int) -> bool:
        """Trigger celebration if cooldown allows.

        Uses Redis for cooldown tracking when available (Story 8-3, AC-6),
        with fallback to in-memory storage.

        Args:
            conversation_id: Conversation UUID
            streak: Current streak count

        Returns:
            True if celebration was triggered, False if blocked by cooldown
        """
        # Check cooldown using Redis or in-memory fallback (Story 8-3, AC-6)
        if self._is_on_cooldown(conversation_id):
            remaining = self._get_cooldown_remaining(conversation_id)
            logger.info(
                f"Celebration skipped for {conversation_id} "
                f"(cooldown: {remaining}s remaining)"
            )
            return False

        # Trigger celebration
        achievement_type = f"{streak}-in-a-row"

        try:
            socketio.emit('celebration:trigger', {
                'achievement_type': achievement_type,
                'streak': streak,
                'timestamp': datetime.now().isoformat()
            }, room=conversation_id)

            # Set cooldown using Redis or in-memory fallback (Story 8-3, AC-6)
            self._set_cooldown(conversation_id)

            logger.info(f"Celebration triggered for {conversation_id}: {achievement_type}")
            return True

        except Exception as e:
            logger.error(f"Failed to emit celebration event: {e}")
            return False

    def _is_on_cooldown(self, conversation_id: str) -> bool:
        """Check if celebration is on cooldown (Story 8-3, AC-6).

        Uses Redis when available, falls back to in-memory.

        Args:
            conversation_id: Conversation UUID

        Returns:
            True if on cooldown, False otherwise
        """
        # Try Redis first
        if self._redis_service and self._redis_service.is_connected():
            return self._redis_service.is_celebration_on_cooldown(conversation_id)

        # Fallback to in-memory
        if conversation_id in self._in_memory_cooldowns:
            last_celebration = self._in_memory_cooldowns[conversation_id]
            time_since = datetime.now() - last_celebration
            return time_since < timedelta(minutes=2)

        return False

    def _set_cooldown(self, conversation_id: str) -> None:
        """Set celebration cooldown (Story 8-3, AC-6).

        Uses Redis when available (2-minute TTL), falls back to in-memory.

        Args:
            conversation_id: Conversation UUID
        """
        # Try Redis first
        if self._redis_service and self._redis_service.is_connected():
            self._redis_service.set_celebration_cooldown(conversation_id)
            return

        # Fallback to in-memory
        self._in_memory_cooldowns[conversation_id] = datetime.now()

    def _get_cooldown_remaining(self, conversation_id: str) -> int:
        """Get remaining cooldown time in seconds (Story 8-3, AC-6).

        Args:
            conversation_id: Conversation UUID

        Returns:
            Remaining seconds, or 0 if no cooldown
        """
        # Try Redis first
        if self._redis_service and self._redis_service.is_connected():
            remaining = self._redis_service.get_celebration_cooldown_remaining(conversation_id)
            return remaining if remaining else 0

        # Fallback to in-memory
        if conversation_id in self._in_memory_cooldowns:
            last_celebration = self._in_memory_cooldowns[conversation_id]
            time_since = datetime.now() - last_celebration
            remaining = 120 - time_since.total_seconds()
            return max(0, int(remaining))

        return 0

    def get_streak(self, conversation_id: str) -> int:
        """Get current streak from conversation context.

        Args:
            conversation_id: Conversation UUID

        Returns:
            Current streak count
        """
        # This would typically retrieve from database or cache
        # For now, return 0 as placeholder
        return 0

    def reset_streak(self, conversation_id: str) -> None:
        """Reset streak for conversation.

        Args:
            conversation_id: Conversation UUID
        """
        logger.info(f"Streak reset for {conversation_id}")
        # Reset would be persisted to database/cache

    def clear_cooldown(self, conversation_id: str) -> None:
        """Clear celebration cooldown for conversation (Story 8-3, AC-6).

        Uses Redis when available, falls back to in-memory.

        Args:
            conversation_id: Conversation UUID
        """
        # Try Redis first
        if self._redis_service and self._redis_service.is_connected():
            self._redis_service.clear_celebration_cooldown(conversation_id)
            logger.info(f"Cooldown cleared for {conversation_id} (Redis)")
            return

        # Fallback to in-memory
        if conversation_id in self._in_memory_cooldowns:
            del self._in_memory_cooldowns[conversation_id]
            logger.info(f"Cooldown cleared for {conversation_id} (in-memory)")
