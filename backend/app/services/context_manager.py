"""Conversation Context Manager - maintains conversation history and context."""
import logging
from typing import List, Optional
from app.models import Message, Conversation
from app.extensions import db

logger = logging.getLogger(__name__)


class ConversationContextManager:
    """Manages conversation context for better Socratic responses."""

    def __init__(self, max_context_messages: int = 10):
        """Initialize context manager.

        Args:
            max_context_messages: Maximum number of recent messages to include in context
        """
        self.max_context_messages = max_context_messages

    def get_conversation_context(
        self,
        conversation_id: str,
        include_last_n: Optional[int] = None
    ) -> str:
        """Get conversation context as formatted string.

        Args:
            conversation_id: UUID of conversation
            include_last_n: Number of recent messages to include (default: max_context_messages)

        Returns:
            Formatted conversation context string
        """
        n_messages = include_last_n or self.max_context_messages

        logger.info(f"[CONTEXT] Retrieving context for conversation_id={conversation_id}, type={type(conversation_id)}, n_messages={n_messages}")

        # Get recent messages
        messages = db.session.query(Message)\
            .filter_by(conversation_id=conversation_id)\
            .order_by(Message.created_at.desc())\
            .limit(n_messages)\
            .all()

        logger.info(f"[CONTEXT] Retrieved {len(messages)} messages from database")

        if not messages:
            logger.warning(f"[CONTEXT] No messages found for conversation {conversation_id}")
            return ""

        # Reverse to get chronological order
        messages = list(reversed(messages))

        # Format as conversation
        context_lines = []
        for msg in messages:
            role = msg.role.value.capitalize()
            preview = msg.content[:50] + '...' if len(msg.content) > 50 else msg.content
            context_lines.append(f"{role}: {msg.content}")
            logger.debug(f"[CONTEXT] Added message: {role}: {preview}")

        result = "\n".join(context_lines)
        logger.info(f"[CONTEXT] Formatted context: {len(result)} characters, {len(context_lines)} messages")
        return result

    def extract_student_intent(self, student_message: str) -> dict:
        """Extract student's learning intent and difficulty areas.

        Args:
            student_message: Student's question or statement

        Returns:
            Dictionary with intent analysis
        """
        # Simple keyword-based intent detection
        intent = {
            'is_question': '?' in student_message,
            'is_stuck': any(word in student_message.lower() for word in [
                "don't understand", "confused", "stuck", "don't know", "help"
            ]),
            'is_verification': any(word in student_message.lower() for word in [
                "is this right", "correct", "did i", "check my"
            ]),
            'mentions_concept': self._extract_math_concepts(student_message),
            'has_attempt': any(word in student_message.lower() for word in [
                "i think", "i tried", "i got", "my answer"
            ])
        }

        return intent

    def _extract_math_concepts(self, message: str) -> List[str]:
        """Extract mentioned math concepts from message.

        Args:
            message: Student message

        Returns:
            List of detected math concepts
        """
        concepts = []
        message_lower = message.lower()

        concept_keywords = {
            'algebra': ['variable', 'equation', 'solve', 'x', 'y'],
            'arithmetic': ['add', 'subtract', 'multiply', 'divide', 'sum', 'difference'],
            'fractions': ['fraction', 'numerator', 'denominator', 'half', 'third'],
            'exponents': ['exponent', 'power', 'square', 'cube', 'squared'],
            'linear_equations': ['slope', 'y-intercept', 'line', 'graph'],
            'quadratic': ['quadratic', 'parabola', 'factor', 'roots'],
        }

        for concept, keywords in concept_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                concepts.append(concept)

        return concepts

    def build_context_summary(
        self,
        conversation_id: str,
        current_message: str
    ) -> dict:
        """Build comprehensive context summary for tutor response generation.

        Args:
            conversation_id: Conversation UUID
            current_message: Current student message

        Returns:
            Context summary dictionary
        """
        logger.info(f"[CONTEXT_SUMMARY] Building context summary for conversation {conversation_id}")

        # Get conversation history
        history = self.get_conversation_context(conversation_id, include_last_n=5)
        logger.info(f"[CONTEXT_SUMMARY] Got history: {len(history)} characters")

        # Analyze current message
        intent = self.extract_student_intent(current_message)

        # Get conversation metadata
        conversation = db.session.get(Conversation, conversation_id)
        message_count = db.session.query(Message)\
            .filter_by(conversation_id=conversation_id)\
            .count()

        logger.info(f"[CONTEXT_SUMMARY] Message count: {message_count}, is_first: {message_count == 0}")

        summary = {
            'conversation_id': str(conversation_id),
            'title': conversation.title if conversation else None,
            'message_count': message_count,
            'recent_history': history,
            'student_intent': intent,
            'current_message': current_message,
            'is_first_message': message_count == 0
        }

        logger.info(f"[CONTEXT_SUMMARY] Built summary with recent_history length: {len(summary['recent_history'])}")
        return summary
