"""Conversation Context Manager - maintains conversation history and context.

Enhanced with OCR context integration (Story 8-4):
- Include image OCR results in conversation context
- Low-confidence indicator for uncertain extractions
- Format image context for tutor awareness
"""
import logging
from typing import List, Optional, Dict, Any
from app.models import Message, Conversation
from app.extensions import db

logger = logging.getLogger(__name__)

# Confidence threshold for OCR results (AC-3)
LOW_CONFIDENCE_THRESHOLD = 0.8


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

        # Format as conversation with OCR context (Story 8-4, AC-3)
        context_lines = []
        for msg in messages:
            role = msg.role.value.capitalize()
            preview = msg.content[:50] + '...' if len(msg.content) > 50 else msg.content

            # Check for OCR data in message metadata (AC-3)
            if msg.message_metadata and msg.message_metadata.get('ocr_result'):
                image_context = self._format_image_context(msg.message_metadata)
                context_lines.append(image_context)
                logger.debug(f"[CONTEXT] Added image context for message")

            context_lines.append(f"{role}: {msg.content}")
            logger.debug(f"[CONTEXT] Added message: {role}: {preview}")

        result = "\n".join(context_lines)
        logger.info(f"[CONTEXT] Formatted context: {len(result)} characters, {len(context_lines)} messages")
        return result

    def _format_image_context(self, metadata: Dict[str, Any]) -> str:
        """Format image OCR metadata for conversation context (Story 8-4, AC-3).

        Args:
            metadata: Message metadata containing OCR result

        Returns:
            Formatted image context string for tutor awareness
        """
        ocr_result = metadata.get('ocr_result', '')
        confidence = metadata.get('ocr_confidence', 0.9)
        problem_type = metadata.get('problem_type', 'unknown')
        latex = metadata.get('ocr_latex', '')

        # Build context string with confidence indicator
        if confidence < LOW_CONFIDENCE_THRESHOLD:
            context = f"[Student uploaded image (low confidence {confidence:.0%}): {ocr_result}]"
            logger.info(f"[CONTEXT] Low confidence image context: {confidence:.0%}")
        else:
            context = f"[Student uploaded image: {ocr_result}]"

        # Add problem type if detected
        if problem_type and problem_type != 'unknown':
            context = context.replace(']', f' - {problem_type} problem]')

        # Add LaTeX if available and different from plain text
        if latex and latex != ocr_result:
            context = context.replace(']', f' (LaTeX: {latex})]')

        return context

    def format_geometry_context(self, geometry_result: Dict[str, Any]) -> str:
        """Format geometry OCR result for tutor context (Story 8-5 preparation).

        Args:
            geometry_result: GeometryResult dict with shapes, relationships, etc.

        Returns:
            Formatted geometry context string
        """
        parts = ["[Student uploaded geometry diagram:"]

        # Add shapes
        shapes = geometry_result.get('shapes', [])
        if shapes:
            shape_desc = ", ".join([
                f"{s.get('type', 'shape')} {s.get('labels', [])}"
                for s in shapes[:3]  # Limit to 3 shapes for context brevity
            ])
            parts.append(f"  Shapes: {shape_desc}")

        # Add relationships
        relationships = geometry_result.get('relationships', [])
        if relationships:
            rel_desc = ", ".join([
                f"{r.get('type', 'related')} ({r.get('elements', [])})"
                for r in relationships[:2]
            ])
            parts.append(f"  Relationships: {rel_desc}")

        # Add problem text
        problem_text = geometry_result.get('problem_text', [])
        if problem_text:
            parts.append(f"  Problem: {' '.join(problem_text)}")

        # Add given information
        given = geometry_result.get('given_information', [])
        if given:
            parts.append(f"  Given: {', '.join(given[:3])}")

        parts.append("]")
        return "\n".join(parts)

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
