"""Answer Checker Service - validates student answers against correct solutions."""
import logging
import re
from typing import Dict, Any, Optional, Tuple
from sympy import sympify, simplify, solve, Abs, N, symbols, Eq
from sympy.core.numbers import Float, Integer, Rational

logger = logging.getLogger(__name__)


class AnswerChecker:
    """Service for checking if student answers are correct."""

    TOLERANCE = 0.001  # Numerical tolerance for comparisons

    def __init__(self):
        """Initialize answer checker."""
        logger.info("Initialized Answer Checker")

    def extract_equation_from_history(self, conversation_history: str) -> Optional[str]:
        """Extract the most recent equation being solved from conversation history.

        Args:
            conversation_history: Recent conversation text

        Returns:
            Equation string (e.g., "x + 3 = 5") or None
        """
        if not conversation_history:
            return None

        # Look for equations in the conversation
        # Pattern: variable + operator + number = number or similar patterns
        equation_patterns = [
            r'([a-z]\s*[+\-*/]\s*\d+\s*=\s*\d+)',  # x + 3 = 5
            r'(\d+\s*[+\-*/]\s*[a-z]\s*=\s*\d+)',  # 3 + x = 5
            r'(\d+\s*\*?\s*[a-z]\s*=\s*\d+)',      # 2x = 10 or 2*x = 10
            r'([a-z]\s*=\s*\d+)',                  # x = 5 (already solved)
        ]

        # Search through the history in reverse (most recent first)
        lines = conversation_history.split('\n')
        for line in reversed(lines):
            line_lower = line.lower()
            for pattern in equation_patterns:
                match = re.search(pattern, line_lower)
                if match:
                    equation = match.group(1).strip()
                    # Filter out if this looks like a student answer (just "x = number")
                    if re.match(r'^[a-z]\s*=\s*-?\d+(\.\d+)?$', equation):
                        continue
                    logger.info(f"[ANSWER_CHECK] Extracted equation from history: {equation}")
                    return equation

        return None

    def parse_student_answer(self, student_message: str) -> Optional[Dict[str, Any]]:
        """Parse the student's answer to extract variable and value.

        Args:
            student_message: The student's message

        Returns:
            Dict with 'variable' and 'value' or None
        """
        message = student_message.lower().strip()

        # Pattern 1: "x = 5" format
        match = re.match(r'^([a-z])\s*=\s*(-?\d+(?:\.\d+)?)$', message)
        if match:
            return {
                'variable': match.group(1),
                'value': float(match.group(2))
            }

        # Pattern 2: Just a number (assume variable is x)
        match = re.match(r'^(-?\d+(?:\.\d+)?)$', message)
        if match:
            return {
                'variable': 'x',  # Default to x
                'value': float(match.group(1))
            }

        return None

    def solve_equation(self, equation_str: str, variable: str = 'x') -> Optional[float]:
        """Solve an equation for the given variable.

        Args:
            equation_str: Equation string (e.g., "x + 3 = 5" or "2x = 10")
            variable: Variable to solve for

        Returns:
            Solution value or None if unsolvable
        """
        try:
            # Clean up the equation
            equation_str = equation_str.replace(' ', '')

            # Handle implicit multiplication (2x -> 2*x)
            equation_str = re.sub(r'(\d)([a-z])', r'\1*\2', equation_str)

            # Split by equals sign
            if '=' not in equation_str:
                logger.warning(f"No equals sign in equation: {equation_str}")
                return None

            left, right = equation_str.split('=')

            # Parse both sides
            var = symbols(variable)
            left_expr = sympify(left, locals={variable: var})
            right_expr = sympify(right, locals={variable: var})

            # Create equation
            equation = Eq(left_expr, right_expr)

            # Solve for the variable
            solutions = solve(equation, var)

            if not solutions:
                logger.warning(f"No solutions found for equation: {equation_str}")
                return None

            # Return the first solution as a float
            solution = solutions[0]
            solution_float = float(N(solution))

            logger.info(f"[ANSWER_CHECK] Solved {equation_str} for {variable} = {solution_float}")
            return solution_float

        except Exception as e:
            logger.error(f"Error solving equation '{equation_str}': {e}")
            return None

    def check_answer(
        self,
        student_message: str,
        conversation_history: str
    ) -> Tuple[bool, str, Optional[float]]:
        """Check if student's answer is correct.

        Args:
            student_message: Student's answer message
            conversation_history: Recent conversation history

        Returns:
            Tuple of (is_correct, explanation, expected_answer)
        """
        # Parse student answer
        student_answer = self.parse_student_answer(student_message)
        if not student_answer:
            return False, "Could not parse student answer", None

        # Extract equation from history
        equation = self.extract_equation_from_history(conversation_history)
        if not equation:
            logger.warning("[ANSWER_CHECK] Could not extract equation from history")
            # If we can't find the equation, assume it's correct
            # This prevents breaking the flow for edge cases
            return True, "No equation found to validate against", None

        # Solve the equation
        expected_answer = self.solve_equation(equation, student_answer['variable'])
        if expected_answer is None:
            logger.warning(f"[ANSWER_CHECK] Could not solve equation: {equation}")
            # If we can't solve it, assume correct
            return True, "Could not solve equation", None

        # Compare answers
        student_value = student_answer['value']
        is_correct = abs(student_value - expected_answer) < self.TOLERANCE

        if is_correct:
            explanation = f"Correct! {student_answer['variable']} = {expected_answer}"
        else:
            explanation = f"Incorrect. Expected {student_answer['variable']} = {expected_answer}, got {student_value}"

        logger.info(f"[ANSWER_CHECK] Student: {student_value}, Expected: {expected_answer}, Correct: {is_correct}")

        return is_correct, explanation, expected_answer
