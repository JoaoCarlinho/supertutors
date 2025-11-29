"""Socratic Guard Service - ensures tutor never gives direct answers."""
import logging
import os
import re
from typing import Dict, Tuple, Optional
from ollama import Client
from openai import OpenAI

logger = logging.getLogger(__name__)

# Validation patterns for direct answers
# Note: These patterns should NOT match when acknowledging student's correct answer
DIRECT_ANSWER_PATTERNS = [
    r'\bthe answer is\s+[^\s]',  # "the answer is 5" but not "the answer is correct"
    r'\bthe solution is\s+\d+',
    r'\bthe result is\s+\d+',
    r'\bstep\s+\d+:',
    r'\bfirst,\s+\w+\.\s+then,',
    r'\buse\s+the\s+formula',
    r'\bapply\s+the\s+formula',
    r'\bsubstitute\s+\d+',
    r'\bplug\s+in\s+\d+',
]

# Patterns that indicate tutor is GIVING the answer (forbidden)
# These are checked only if no acknowledgment phrases are present
GIVING_ANSWER_PATTERNS = [
    r'\bx\s*=\s*\d+',
    r'\by\s*=\s*\d+',
    r'\bz\s*=\s*\d+',
    r'\bequals\s*\d+',
    r'\b=\s*\d+\b',
]

# Phrases that indicate acknowledgment (allowed)
ACKNOWLEDGMENT_PHRASES = [
    r'\bcorrect\b',
    r'\bexactly\b',
    r'\bperfect\b',
    r'\bexcellent\b',
    r'\bgreat job\b',
    r'\bwell done\b',
    r'\byou\'?ve got it\b',
    r'\byou\'?ve solved it\b',
    r'\bthat\'?s right\b',
    r'\byes\b',
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

    def __init__(self, model_name: str = "gpt-4o-mini", max_retries: int = 3, use_openai: bool = True):
        """Initialize Socratic Guard.

        Args:
            model_name: Model to use (OpenAI model name or Ollama model name)
            max_retries: Maximum number of regeneration attempts
            use_openai: If True, use OpenAI API; if False, use Ollama
        """
        self.model_name = model_name
        self.max_retries = max_retries
        self.use_openai = use_openai

        if use_openai:
            api_key = os.environ.get('OPENAI_API_KEY')
            if not api_key:
                logger.error("OPENAI_API_KEY not found, falling back to Ollama")
                self.use_openai = False
                self.model_name = "llama3.2:latest"
                base_url = os.environ.get('OLLAMA_BASE_URL', 'http://localhost:11434')
                self.client = Client(host=base_url)
            else:
                self.client = OpenAI(api_key=api_key)
                logger.info(f"Initialized Socratic Guard with OpenAI model {model_name}")
        else:
            base_url = os.environ.get('OLLAMA_BASE_URL', 'http://localhost:11434')
            self.client = Client(host=base_url)
            logger.info(f"Initialized Socratic Guard with Ollama model {model_name}")

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

        # First check if this is an acknowledgment response
        has_acknowledgment = any(
            re.search(pattern, response_lower)
            for pattern in ACKNOWLEDGMENT_PHRASES
        )

        # Check general direct answer patterns
        for pattern in DIRECT_ANSWER_PATTERNS:
            if re.search(pattern, response_lower):
                return False, f"Matched pattern: {pattern}", 0.9

        # Check "giving answer" patterns only if NOT acknowledging
        if not has_acknowledgment:
            for pattern in GIVING_ANSWER_PATTERNS:
                if re.search(pattern, response_lower):
                    return False, f"Tutor is giving answer: {pattern}", 0.9

        # Count keywords (but be lenient if acknowledging)
        keyword_count = sum(
            1 for keyword in DIRECT_ANSWER_KEYWORDS
            if keyword in response_lower
        )

        if has_acknowledgment:
            # Allow more keywords when acknowledging correct answer
            if keyword_count >= 5:
                return False, f"Too many direct answer keywords even with acknowledgment ({keyword_count})", 0.7
            return True, "Acknowledgment response with acceptable keywords", 0.8
        else:
            # Strict checking when not acknowledging
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
        """LLM-based validation using OpenAI or Ollama.

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
            if self.use_openai:
                # OpenAI API call
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[{'role': 'user', 'content': prompt}],
                    temperature=0.1,
                    max_tokens=150
                )
                result_text = response.choices[0].message.content
            else:
                # Ollama API call
                response = self.client.chat(
                    model=self.model_name,
                    messages=[{'role': 'user', 'content': prompt}],
                    options={'temperature': 0.1}
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
        attempt: int = 1,
        math_context: Optional[Dict] = None,
        is_correct_answer: Optional[bool] = None
    ) -> str:
        """Generate a Socratic tutor response.

        Args:
            student_message: Student's question
            conversation_context: Previous conversation history
            attempt: Current generation attempt (1-3)
            math_context: Optional SymPy computation results

        Returns:
            Generated Socratic response
        """
        logger.info(f"[SOCRATIC] Generating response, attempt {attempt}")
        logger.info(f"[SOCRATIC] Conversation context provided: {bool(conversation_context)}, length: {len(conversation_context) if conversation_context else 0}")
        if conversation_context:
            logger.debug(f"[SOCRATIC] Context preview: {conversation_context[:200]}")

        # Build prompt with increasing emphasis on Socratic method
        emphasis = ["", "IMPORTANT: ", "CRITICAL: "][min(attempt - 1, 2)]

        # Detect if this message came from OCR/Vision (image or drawing)
        is_from_image = self._detect_ocr_content(student_message)

        # Build math context section if available
        math_info = ""
        if math_context and math_context.get('detected'):
            math_info = "\n\nMATH ANALYSIS (use this to ask informed questions):\n"
            for expr in math_context.get('expressions', []):
                math_info += f"- Expression: {expr['original']}\n"
                if expr.get('simplified'):
                    math_info += f"  Simplified: {expr['simplified']}\n"
                if expr.get('solutions'):
                    math_info += f"  Solutions exist: {', '.join(expr['solutions'])}\n"
                if expr.get('steps'):
                    math_info += f"  Solution steps: {len(expr['steps'])} steps available\n"
            math_info += "\nUse this information to ask questions that guide the student toward these insights, but NEVER reveal the answers directly.\n"

        # Image awareness instructions for OCR content (Story 8-4, AC-6)
        ocr_instruction = ""
        if is_from_image:
            # Check if this is geometry content (Story 8-5, AC-6)
            is_geometry = self._detect_geometry_content(student_message)

            if is_geometry:
                ocr_instruction = """

⚠️ GEOMETRY DIAGRAM DETECTED - MANDATORY ACTION REQUIRED:
This content came from an uploaded geometric diagram.

GEOMETRY AWARENESS GUIDELINES (Story 8-5):
- Reference the shapes naturally: "I see you have a triangle with sides 3, 4, and 5..."
- Reference measurements: "Looking at angle ABC which measures 90 degrees..."
- Reference relationships: "I notice that lines AB and CD are parallel..."
- If you see a right angle (marked with a small square), acknowledge it explicitly
- If confidence is low (<80%), ask for confirmation: "I think side AB is 5cm, is that correct?"
- Ask what they're trying to find or prove BEFORE providing guidance
- Example: "I see Triangle ABC with a right angle at C. What would you like to find - the area, the hypotenuse, or something else?"

GEOMETRY-SPECIFIC QUESTIONS TO ASK:
- "What type of triangle/shape do you see here?"
- "What theorem or property might apply to this shape?"
- "What do you know about the relationship between these elements?"
- "Can you identify any special properties (right angles, parallel lines, congruent sides)?"

Do not skip these steps - acknowledge the geometry diagram first."""
            else:
                ocr_instruction = """

⚠️ IMAGE/DRAWING DETECTED - MANDATORY ACTION REQUIRED:
This content came from an uploaded image or drawing.

IMAGE AWARENESS GUIDELINES:
- Reference the uploaded content naturally: "I see you wrote..." or "Looking at the equation you uploaded..."
- If confidence is mentioned as low (<80%), ask for confirmation: "I think you wrote X, is that correct?"
- You MUST ask the student what they're trying to solve or calculate BEFORE providing any other guidance.
- Example good response: "I see you've written 3x + 2 = 5. What would you like to do with this equation?"

Do not skip these steps - acknowledge the image first."""

        # Build context section (avoid backslashes in f-string expressions)
        context_section = ""
        if conversation_context:
            context_section = "Previous conversation:\n" + conversation_context + "\n"

        # Build critical instructions based on whether we have context
        if not conversation_context:
            critical_instructions = "This is the START of a new conversation. The student is asking for help with a problem. Guide them through solving it step-by-step using the Socratic method. Ask what operation they think should be performed first to solve the equation."
        elif is_correct_answer is True:
            # Student provided CORRECT final answer
            critical_instructions = """The student just provided a CORRECT final answer!

CELEBRATE their success! Confirm they found the correct answer WITHOUT restating it.
→ Say things like "Excellent! You've solved it!" or "Perfect! That's the correct answer!" or "Yes, you've got it!"
→ Do NOT repeat their answer back to them (e.g., don't say "x = 1 is correct" - just say "That's correct!")
→ Then IMMEDIATELY ask: "Would you like to try another problem?" or "Ready for another question?"
→ DO NOT suggest verification or ask follow-up questions about the solution."""
        elif is_correct_answer is False:
            # Student provided INCORRECT final answer
            critical_instructions = """The student just provided an INCORRECT final answer.

DO NOT tell them the answer! Instead, gently guide them to reconsider:
→ Say something like "Hmm, let's double-check that. Can you walk me through your calculation?"
→ Or "That's not quite right. Let's go back - what did you get when you [operation]?"
→ Guide them to identify where they made an error without giving away the answer.
→ Be encouraging and supportive - everyone makes mistakes!"""
        else:
            critical_instructions = """This is a CONTINUING conversation. Review the previous messages above.

IMPORTANT: Look at the student's LAST response carefully:

1. **Is it a QUESTION asking for help?** (e.g., "what is the answer to...", "how do I solve...")
   → They haven't solved anything yet! Guide them to start solving step-by-step.
   → Ask what operation they should perform first.

2. **Did they identify an operation?** (e.g., "subtract 3", "divide by 2")
   → Ask them to COMPUTE the result of that operation
   → Example: "What do you get when you subtract 3 from both sides?"

3. **Did they give an intermediate result?** (e.g., "2x = 4")
   → Ask what the NEXT SPECIFIC operation should be
   → Example: "Good! Now what operation will isolate x?"

4. **Are they stuck or asking for help?**
   → Ask a more specific question about the current step
   → Guide them to the operation they need

NEVER skip ahead. NEVER be vague. Make them compute EACH intermediate step."""

        prompt = f"""{emphasis}You are a Socratic math tutor for the following subjects:
1 - addition
2 - subtraction
3 - multiplication
4 - division
5 - geometry
6 - algebra

Your role is to guide students to discover answers themselves through questions - NEVER give direct answers.

TONE: Be naturally encouraging and supportive, but vary your language. Avoid starting every response with the same praise phrases like "Great thinking!" or "Excellent observation!" Mix it up and be authentic.

FORBIDDEN behaviors:
- NEVER give numerical answers (e.g., "x = 5")
- NEVER provide step-by-step solutions
- NEVER state formulas with values substituted
- NEVER say "the answer is..." or "the solution is..."
- NEVER skip steps or ask vague questions like "what happens if we do something?"
- NEVER be repetitive with encouragement phrases

REQUIRED behaviors - FOLLOW THIS SEQUENCE:
1. Ask what SPECIFIC operation to perform (e.g., "What should we subtract from both sides?")
2. After student identifies operation, ask for the INTERMEDIATE RESULT (e.g., "What do you get after subtracting 3 from both sides?")
3. Ask about the NEXT specific operation needed
4. Repeat: operation → result → next operation → result
5. Guide step-by-step, making student compute EACH intermediate state

CRITICAL: Make the student figure out and state:
- The specific operation (subtract what? divide by what?)
- The intermediate result after each operation (what equals what?)
- Build understanding through computing each step themselves

{context_section}
{math_info}

Student: {student_message}

CRITICAL INSTRUCTIONS:

{critical_instructions}
{ocr_instruction}

Respond as a Socratic tutor (2-3 sentences max):"""

        try:
            if self.use_openai:
                # OpenAI API call
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[{'role': 'user', 'content': prompt}],
                    temperature=0.7,
                    max_tokens=200
                )
                return response.choices[0].message.content.strip()
            else:
                # Ollama API call
                response = self.client.chat(
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

    def detect_final_answer(self, student_message: str, math_context: Optional[Dict] = None) -> bool:
        """Detect if student provided a final answer (e.g., "x = 1").

        Args:
            student_message: The student's message
            math_context: Optional math analysis context

        Returns:
            True if this appears to be a final answer
        """
        message_lower = student_message.lower().strip()

        # Exclude questions - if message contains question words, it's not a final answer
        question_indicators = ['what', 'how', 'why', 'when', 'where', 'which', 'who', '?']
        if any(indicator in message_lower for indicator in question_indicators):
            return False

        # Pattern 1: Simple variable assignment (x = number)
        import re
        if re.match(r'^[a-z]\s*=\s*-?\d+(\.\d+)?$', message_lower):
            return True

        # Pattern 2: Just a number (could be final answer)
        if re.match(r'^-?\d+(\.\d+)?$', message_lower):
            return True

        # Pattern 3: Math context shows this is a solution (but only if it's a short message)
        # Long messages with equations are likely questions, not answers
        if len(message_lower) < 15 and math_context and math_context.get('detected'):
            for expr in math_context.get('expressions', []):
                original = expr.get('original', '').lower()
                # Check if it's a simple equation statement (not a full question)
                if expr.get('type') == 'equation' and '=' in original and len(original) < 15:
                    return True

        return False

    def generate_validated_response(
        self,
        student_message: str,
        conversation_context: Optional[str] = None,
        math_context: Optional[Dict] = None,
        is_correct_answer: Optional[bool] = None
    ) -> Dict[str, any]:
        """Generate and validate Socratic response with retry logic.

        Args:
            student_message: Student's question
            conversation_context: Previous conversation history
            math_context: Optional SymPy computation results
            is_correct_answer: If this is a final answer, whether it's correct (None if not a final answer)

        Returns:
            Dictionary with response, validation_passed, attempts, etc.
        """
        # Detect if this is a final answer
        is_final_answer = is_correct_answer is not None

        # If this is a celebration or correction response, skip validation
        # (validation is meant to prevent giving away answers, not prevent acknowledgment)
        if is_correct_answer is not None:
            logger.info(f"Skipping validation for {'celebration' if is_correct_answer else 'correction'} response")
            response = self.generate_socratic_response(
                student_message,
                conversation_context,
                1,
                math_context,
                is_correct_answer
            )
            return {
                'response': response,
                'validation_passed': True,
                'attempts': 1,
                'confidence': 1.0,
                'reason': 'Validation skipped for acknowledgment response',
                'is_final_answer': is_final_answer
            }

        for attempt in range(1, self.max_retries + 1):
            logger.info(f"Generating response, attempt {attempt}/{self.max_retries}")

            # Generate response
            response = self.generate_socratic_response(
                student_message,
                conversation_context,
                attempt,
                math_context,
                is_correct_answer
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
                    'reason': reason,
                    'is_final_answer': is_final_answer
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
            'reason': 'Used fallback after max retries',
            'is_final_answer': is_final_answer
        }

    def _detect_ocr_content(self, message: str) -> bool:
        """Detect if message content came from OCR/Vision extraction.

        Looks for patterns that indicate the message was extracted from
        an image or drawing by the vision service.

        Args:
            message: The student message to analyze

        Returns:
            True if message appears to be from OCR extraction
        """
        # Check for OCR output patterns from our vision service
        ocr_indicators = [
            'Linear equation:',
            'ALGEBRA:',
            'GEOMETRY:',
            'ARITHMETIC:',
            'Right triangle',
            'This image shows',
            'equation:',
            'problem:',
            'Given values:',
            'Find:',
            'Pythagorean theorem',
        ]

        message_lower = message.lower()

        # Check if any OCR indicator is present
        for indicator in ocr_indicators:
            if indicator.lower() in message_lower:
                return True

        # Check for LaTeX patterns (our OCR always uses these)
        if '$' in message and any(c.isalpha() for c in message):
            # Has LaTeX delimiters and variables - likely from OCR
            return True

        return False

    def _detect_geometry_content(self, message: str) -> bool:
        """Detect if message content is geometry-related (Story 8-5, AC-6).

        Looks for patterns that indicate the message contains geometric
        shapes, measurements, or relationships from geometry OCR.

        Args:
            message: The student message to analyze

        Returns:
            True if message appears to contain geometry content
        """
        message_lower = message.lower()

        # Geometry shape indicators
        shape_keywords = [
            'triangle', 'circle', 'rectangle', 'square', 'polygon',
            'parallelogram', 'trapezoid', 'rhombus', 'pentagon',
            'hexagon', 'octagon', 'quadrilateral', 'line segment',
            'ray', 'arc', 'chord', 'tangent', 'secant'
        ]

        # Geometry measurement indicators
        measurement_keywords = [
            'angle', 'degree', 'radius', 'diameter', 'circumference',
            'perimeter', 'area', 'volume', 'surface area', 'height',
            'base', 'hypotenuse', 'leg', 'altitude', 'median',
            'side length', 'vertex', 'vertices'
        ]

        # Geometry relationship indicators
        relationship_keywords = [
            'parallel', 'perpendicular', 'congruent', 'similar',
            'bisect', 'bisector', 'midpoint', 'inscribed',
            'circumscribed', 'tangent to', 'intersect'
        ]

        # Geometry theorem/property indicators
        theorem_keywords = [
            'pythagorean', 'theorem', 'sohcahtoa', 'sine', 'cosine',
            'tangent', 'isosceles', 'equilateral', 'scalene',
            'right angle', 'acute', 'obtuse', 'supplementary',
            'complementary', 'vertical angles', 'corresponding'
        ]

        # Check for any geometry indicators
        all_keywords = (
            shape_keywords + measurement_keywords +
            relationship_keywords + theorem_keywords
        )

        for keyword in all_keywords:
            if keyword in message_lower:
                return True

        # Check for geometry notation patterns
        geometry_patterns = [
            r'triangle\s+[A-Z]{3}',  # Triangle ABC
            r'angle\s+[A-Z]{1,3}',  # Angle A, Angle ABC
            r'∠[A-Z]{1,3}',  # ∠ABC
            r'[A-Z]{2}\s*[|‖]\s*[A-Z]{2}',  # AB || CD (parallel)
            r'[A-Z]{2}\s*[⊥]\s*[A-Z]{2}',  # AB ⊥ CD (perpendicular)
            r'\d+\s*°',  # 90°
            r'\d+\s*degrees?',  # 90 degrees
            r'side\s+[A-Z]{2}',  # side AB
        ]

        for pattern in geometry_patterns:
            if re.search(pattern, message, re.IGNORECASE):
                return True

        return False
