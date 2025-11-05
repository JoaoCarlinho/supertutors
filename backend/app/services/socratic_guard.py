"""Socratic Guard Service - ensures tutor never gives direct answers."""
import logging
import re
from typing import Dict, Tuple, Optional
import ollama

logger = logging.getLogger(__name__)

# Validation patterns for direct answers
DIRECT_ANSWER_PATTERNS = [
    r'\bthe answer is\b',
    r'\bthe solution is\b',
    r'\bthe result is\b',
    r'\bequals?\s*\d+',
    r'\b=\s*\d+',
    r'\bx\s*=\s*\d+',
    r'\by\s*=\s*\d+',
    r'\bstep\s+\d+:',
    r'\bfirst,\s+\w+\.\s+then,',
    r'\buse\s+the\s+formula',
    r'\bapply\s+the\s+formula',
    r'\bsubstitute\s+\d+',
    r'\bplug\s+in\s+\d+',
]

# Keywords that often indicate direct answers
DIRECT_ANSWER_KEYWORDS = [
    'answer', 'solution', 'result', 'equals', 'formula',
    'calculate', 'substitute', 'plug in', 'step 1', 'step 2'
]

# Fallback Socratic questions when validation fails
FALLBACK_QUESTIONS = [
    "What have you tried so far to solve this problem?",
    "What do you think might be the first step?",
    "Can you tell me what you understand about this problem?",
    "What strategies do you know that might help here?",
    "What part of this problem seems most challenging to you?",
]

# Validation prompt template for LLM
VALIDATION_PROMPT_TEMPLATE = """You are a validator for a Socratic tutoring system. Your job is to determine if a tutor response gives a DIRECT ANSWER to a student's question.

A DIRECT ANSWER includes:
- Numerical solutions (e.g., "x = 5", "the answer is 42")
- Step-by-step solutions (e.g., "Step 1: add 2. Step 2: divide by 3")
- Formulas with values substituted (e.g., "substitute 5 into x+2 to get 7")
- Direct statements of the result

A SOCRATIC RESPONSE asks guiding questions without giving answers:
- "What operation do you think you should use?"
- "What happens when you add these two numbers?"
- "How could you check if your answer is correct?"

Student Question: {student_message}

Tutor Response: {tutor_response}

Analyze the tutor response. Respond ONLY with a JSON object:
{{
  "is_direct_answer": true or false,
  "reason": "brief explanation",
  "confidence": 0.0 to 1.0
}}"""


class SocraticGuard:
    """Service to validate that tutor responses are Socratic (no direct answers)."""

    def __init__(self, model_name: str = "llama3.2:latest", max_retries: int = 3):
        """Initialize Socratic Guard.

        Args:
            model_name: Ollama model to use for validation
            max_retries: Maximum number of regeneration attempts
        """
        self.model_name = model_name
        self.max_retries = max_retries
        logger.info(f"Initialized Socratic Guard with model {model_name}")

    def validate_response(
        self,
        student_message: str,
        tutor_response: str,
        use_llm: bool = True
    ) -> Tuple[bool, str, float]:
        """Validate if tutor response is Socratic (no direct answers).

        Args:
            student_message: The student's question
            tutor_response: The tutor's proposed response
            use_llm: Whether to use LLM validation (True) or rule-based only (False)

        Returns:
            Tuple of (is_valid, reason, confidence)
            - is_valid: True if response is Socratic, False if it gives direct answer
            - reason: Explanation of validation result
            - confidence: Confidence score 0.0-1.0
        """
        # First, try rule-based validation (fast)
        rule_is_valid, rule_reason, rule_confidence = self._rule_based_validation(tutor_response)

        # If rule-based is confident it's a direct answer, don't bother with LLM
        if not rule_is_valid and rule_confidence > 0.8:
            logger.info(f"Rule-based validation failed: {rule_reason}")
            return False, rule_reason, rule_confidence

        # Use LLM for more nuanced validation
        if use_llm:
            try:
                llm_is_valid, llm_reason, llm_confidence = self._llm_validation(
                    student_message, tutor_response
                )

                # Combine rule-based and LLM results
                # If either says it's a direct answer with high confidence, reject it
                if not llm_is_valid and llm_confidence > 0.7:
                    return False, llm_reason, llm_confidence

                if not rule_is_valid and not llm_is_valid:
                    avg_confidence = (rule_confidence + llm_confidence) / 2
                    return False, f"Both validators rejected: {llm_reason}", avg_confidence

                # If LLM is confident it's good, trust it
                if llm_is_valid and llm_confidence > 0.7:
                    return True, llm_reason, llm_confidence

            except Exception as e:
                logger.warning(f"LLM validation failed, falling back to rules: {e}")
                return rule_is_valid, rule_reason, rule_confidence

        return rule_is_valid, rule_reason, rule_confidence

    def _rule_based_validation(self, response: str) -> Tuple[bool, str, float]:
        """Rule-based validation using regex and keyword detection.

        Args:
            response: Tutor response to validate

        Returns:
            Tuple of (is_valid, reason, confidence)
        """
        response_lower = response.lower()

        # Check regex patterns
        for pattern in DIRECT_ANSWER_PATTERNS:
            if re.search(pattern, response_lower):
                return False, f"Matched pattern: {pattern}", 0.9

        # Count keywords
        keyword_count = sum(
            1 for keyword in DIRECT_ANSWER_KEYWORDS
            if keyword in response_lower
        )

        if keyword_count >= 3:
            return False, f"Too many direct answer keywords ({keyword_count})", 0.8
        elif keyword_count >= 2:
            return True, f"Some keywords but likely acceptable ({keyword_count})", 0.5

        return True, "No obvious direct answer patterns detected", 0.7

    def _llm_validation(
        self,
        student_message: str,
        tutor_response: str,
        timeout: int = 5
    ) -> Tuple[bool, str, float]:
        """LLM-based validation using Ollama.

        Args:
            student_message: Student's question
            tutor_response: Tutor's response to validate
            timeout: Maximum seconds for LLM call

        Returns:
            Tuple of (is_valid, reason, confidence)
        """
        prompt = VALIDATION_PROMPT_TEMPLATE.format(
            student_message=student_message,
            tutor_response=tutor_response
        )

        try:
            response = ollama.chat(
                model=self.model_name,
                messages=[{'role': 'user', 'content': prompt}],
                options={'temperature': 0.1}  # Low temperature for consistent validation
            )

            result_text = response['message']['content']

            # Parse JSON response
            import json
            try:
                result = json.loads(result_text)
                is_direct = result.get('is_direct_answer', False)
                reason = result.get('reason', 'No reason provided')
                confidence = result.get('confidence', 0.5)

                is_valid = not is_direct
                return is_valid, reason, confidence

            except json.JSONDecodeError:
                logger.warning(f"Failed to parse LLM response as JSON: {result_text}")
                return True, "Validation inconclusive", 0.3

        except Exception as e:
            logger.error(f"LLM validation error: {e}")
            raise

    def generate_socratic_response(
        self,
        student_message: str,
        conversation_context: Optional[str] = None,
        attempt: int = 1
    ) -> str:
        """Generate a Socratic tutor response.

        Args:
            student_message: Student's question
            conversation_context: Previous conversation history
            attempt: Current generation attempt (1-3)

        Returns:
            Generated Socratic response
        """
        # Build prompt with increasing emphasis on Socratic method
        emphasis = ["", "IMPORTANT: ", "CRITICAL: "][min(attempt - 1, 2)]

        prompt = f"""{emphasis}You are a Socratic math tutor for 9th grade algebra. Your role is to guide students to discover answers themselves through questions - NEVER give direct answers.

FORBIDDEN behaviors:
- Giving numerical answers (e.g., "x = 5")
- Providing step-by-step solutions
- Stating formulas with values substituted
- Saying "the answer is..." or "the solution is..."

REQUIRED behaviors:
- Ask guiding questions that lead to understanding
- Help students recall relevant concepts
- Encourage students to try approaches
- Celebrate their thinking process

{"Previous conversation: " + conversation_context if conversation_context else ""}

Student: {student_message}

Respond as a Socratic tutor with a guiding question or hint (2-3 sentences max):"""

        try:
            response = ollama.chat(
                model=self.model_name,
                messages=[{'role': 'user', 'content': prompt}],
                options={'temperature': 0.7}
            )

            return response['message']['content'].strip()

        except Exception as e:
            logger.error(f"Error generating Socratic response: {e}")
            # Return fallback question
            import random
            return random.choice(FALLBACK_QUESTIONS)

    def generate_validated_response(
        self,
        student_message: str,
        conversation_context: Optional[str] = None
    ) -> Dict[str, any]:
        """Generate and validate Socratic response with retry logic.

        Args:
            student_message: Student's question
            conversation_context: Previous conversation history

        Returns:
            Dictionary with response, validation_passed, attempts, etc.
        """
        for attempt in range(1, self.max_retries + 1):
            logger.info(f"Generating response, attempt {attempt}/{self.max_retries}")

            # Generate response
            response = self.generate_socratic_response(
                student_message,
                conversation_context,
                attempt
            )

            # Validate response
            is_valid, reason, confidence = self.validate_response(
                student_message,
                response
            )

            if is_valid:
                logger.info(f"Response validated successfully on attempt {attempt}")
                return {
                    'response': response,
                    'validation_passed': True,
                    'attempts': attempt,
                    'confidence': confidence,
                    'reason': reason
                }

            logger.warning(
                f"Response failed validation on attempt {attempt}: {reason} "
                f"(confidence: {confidence})"
            )

        # All attempts failed, return fallback
        logger.error("All validation attempts failed, using fallback question")
        import random
        fallback = random.choice(FALLBACK_QUESTIONS)

        return {
            'response': fallback,
            'validation_passed': False,
            'attempts': self.max_retries,
            'confidence': 1.0,
            'reason': 'Used fallback after max retries'
        }
