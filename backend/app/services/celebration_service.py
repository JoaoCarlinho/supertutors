"""Celebration Service - manages streak tracking and celebration triggers."""
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from app.extensions import socketio

logger = logging.getLogger(__name__)


class CelebrationService:
    """Service for tracking streaks and triggering celebrations."""

    def __init__(self):
        """Initialize celebration service."""
        self.celebration_cooldowns = {}  # In-memory cooldown tracking
        logger.info("Initialized Celebration service")

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

        Args:
            conversation_id: Conversation UUID
            streak: Current streak count

        Returns:
            True if celebration was triggered, False if blocked by cooldown
        """
        # Check cooldown (2 minutes)
        cooldown_key = conversation_id
        if cooldown_key in self.celebration_cooldowns:
            last_celebration = self.celebration_cooldowns[cooldown_key]
            time_since = datetime.now() - last_celebration

            if time_since < timedelta(minutes=2):
                logger.info(
                    f"Celebration skipped for {conversation_id} "
                    f"(cooldown: {time_since.seconds}s remaining)"
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

            # Update cooldown
            self.celebration_cooldowns[cooldown_key] = datetime.now()

            logger.info(f"Celebration triggered for {conversation_id}: {achievement_type}")
            return True

        except Exception as e:
            logger.error(f"Failed to emit celebration event: {e}")
            return False

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
        """Clear celebration cooldown for conversation.

        Args:
            conversation_id: Conversation UUID
        """
        if conversation_id in self.celebration_cooldowns:
            del self.celebration_cooldowns[conversation_id]
            logger.info(f"Cooldown cleared for {conversation_id}")
