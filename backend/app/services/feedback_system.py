"""Encouraging Feedback System - provides positive reinforcement."""
import logging
import random
from typing import Optional

logger = logging.getLogger(__name__)

# Encouragement phrases for different scenarios
GENERAL_ENCOURAGEMENT = [
    "Great thinking!",
    "You're on the right track!",
    "Excellent observation!",
    "That's a smart approach!",
    "Nice work!",
]

EFFORT_PRAISE = [
    "I can see you're really thinking this through!",
    "Your persistence is impressive!",
    "Keep up that great effort!",
    "I love how you're working through this!",
]

PROGRESS_PRAISE = [
    "You're making great progress!",
    "Look how far you've come!",
    "You're getting closer!",
    "That's a big step forward!",
]

ATTEMPT_ENCOURAGEMENT = [
    "That's a good try! Let's think about it together.",
    "I appreciate your effort! Let's explore this more.",
    "Good attempt! What if we looked at it this way?",
]

CONFUSION_SUPPORT = [
    "It's okay to feel stuck - that's how we learn!",
    "Many students find this tricky at first.",
    "Let's break this down together.",
    "No worries, we'll figure this out!",
]


class EncouragingFeedbackSystem:
    """Generates encouraging feedback to maintain student motivation."""

    def __init__(self):
        """Initialize feedback system."""
        logger.info("Initialized Encouraging Feedback System")

    def generate_encouragement(
        self,
        context: dict,
        feedback_type: Optional[str] = None
    ) -> str:
        """Generate encouraging feedback based on context.

        Args:
            context: Context dictionary with student intent and progress
            feedback_type: Optional specific type of feedback to generate

        Returns:
            Encouraging feedback phrase
        """
        if feedback_type:
            return self._get_specific_encouragement(feedback_type)

        # Choose based on student intent
        intent = context.get('student_intent', {})

        if intent.get('is_stuck'):
            return random.choice(CONFUSION_SUPPORT)
        elif intent.get('is_verification'):
            return random.choice(PROGRESS_PRAISE)
        elif intent.get('has_attempt'):
            return random.choice(EFFORT_PRAISE)
        else:
            return random.choice(GENERAL_ENCOURAGEMENT)

    def _get_specific_encouragement(self, feedback_type: str) -> str:
        """Get specific type of encouragement.

        Args:
            feedback_type: Type of feedback (general, effort, progress, attempt, confusion)

        Returns:
            Encouraging phrase
        """
        feedback_map = {
            'general': GENERAL_ENCOURAGEMENT,
            'effort': EFFORT_PRAISE,
            'progress': PROGRESS_PRAISE,
            'attempt': ATTEMPT_ENCOURAGEMENT,
            'confusion': CONFUSION_SUPPORT,
        }

        phrases = feedback_map.get(feedback_type, GENERAL_ENCOURAGEMENT)
        return random.choice(phrases)

    def wrap_response_with_encouragement(
        self,
        response: str,
        context: dict,
        prepend: bool = True
    ) -> str:
        """Add encouraging feedback to a Socratic response.

        Args:
            response: Original Socratic response
            context: Context dictionary
            prepend: Whether to add encouragement at start (True) or end (False)

        Returns:
            Response with encouragement added
        """
        encouragement = self.generate_encouragement(context)

        if prepend:
            return f"{encouragement} {response}"
        else:
            return f"{response} {encouragement}"
