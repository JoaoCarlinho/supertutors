"""Answer Validation Service - validates student answers using SymPy."""
import logging
from typing import Dict, Any, List, Optional
from sympy import sympify, simplify, solve, Abs, N, symbols, Eq
from sympy.core.numbers import Float, Integer, Rational
from app.services.sympy_service import SymPyService

logger = logging.getLogger(__name__)


class AnswerValidator:
    """Service for validating student answers against expected answers."""

    TOLERANCE = 0.001  # Numerical tolerance for comparisons

    def __init__(self):
        """Initialize answer validator."""
        self.sympy_service = SymPyService()
        logger.info("Initialized Answer Validator")

    def validate_answer(
        self,
        student_answer: str,
        expected_answer: str,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """Validate student answer against expected answer.

        Args:
            student_answer: Student's submitted answer
            expected_answer: Expected correct answer
            context: Optional context (equation, problem statement)

        Returns:
            Validation response with correct flag, answers, and explanation
        """
        try:
            # Parse both answers
            student_parse = self.sympy_service.parse_expression(student_answer)
            expected_parse = self.sympy_service.parse_expression(expected_answer)

            if not student_parse['success']:
                return {
                    'correct': False,
                    'student_answer': student_answer,
                    'expected_answer': expected_answer,
                    'explanation': f"Could not understand your answer: {student_parse['error']}"
                }

            if not expected_parse['success']:
                logger.error(f"Invalid expected answer: {expected_answer}")
                return {
                    'correct': False,
                    'student_answer': student_answer,
                    'expected_answer': expected_answer,
                    'explanation': "There was an error checking your answer. Please try again."
                }

            student_expr = student_parse['result']
            expected_expr = expected_parse['result']

            # Simplify both expressions
            student_simplified = simplify(student_expr)
            expected_simplified = simplify(expected_expr)

            # Check for equivalence
            is_correct, is_approximate = self._check_equivalence(
                student_simplified,
                expected_simplified
            )

            # Generate explanation
            explanation = self._generate_explanation(
                is_correct,
                is_approximate,
                str(student_simplified),
                str(expected_simplified)
            )

            return {
                'correct': is_correct,
                'student_answer': str(student_simplified),
                'expected_answer': str(expected_simplified),
                'explanation': explanation,
                'is_approximate': is_approximate
            }

        except Exception as e:
            logger.error(f"Error validating answer: {e}")
            return {
                'correct': False,
                'student_answer': student_answer,
                'expected_answer': expected_answer,
                'explanation': "An error occurred while checking your answer."
            }

    def _check_equivalence(self, expr1, expr2) -> tuple[bool, bool]:
        """Check if two expressions are equivalent.

        Args:
            expr1: First SymPy expression
            expr2: Second SymPy expression

        Returns:
            Tuple of (is_equivalent, is_approximate)
        """
        try:
            # Try symbolic equivalence first
            difference = simplify(expr1 - expr2)

            # If difference is exactly zero, they're equivalent
            if difference == 0:
                return True, False

            # Try numerical evaluation for approximate equivalence
            try:
                # Substitute any symbols with a test value
                free_symbols = difference.free_symbols
                if free_symbols:
                    # If there are variables, can't do numerical comparison
                    # Check if they're symbolically equal using equals()
                    try:
                        if expr1.equals(expr2):
                            return True, False
                    except:
                        pass
                    return False, False

                # No variables, evaluate numerically
                diff_value = float(N(difference))

                if abs(diff_value) < self.TOLERANCE:
                    return True, True  # Approximately equal

            except (ValueError, TypeError):
                # Can't evaluate numerically
                pass

            return False, False

        except Exception as e:
            logger.warning(f"Error checking equivalence: {e}")
            return False, False

    def _generate_explanation(
        self,
        is_correct: bool,
        is_approximate: bool,
        student_answer: str,
        expected_answer: str
    ) -> str:
        """Generate explanation for validation result.

        Args:
            is_correct: Whether answer is correct
            is_approximate: Whether match is approximate
            student_answer: Student's simplified answer
            expected_answer: Expected simplified answer

        Returns:
            Explanation string
        """
        if is_correct:
            if is_approximate:
                return "Approximately correct! Your answer is very close."
            else:
                return "Correct! Well done."
        else:
            return f"Not quite. Your answer simplifies to {student_answer}, but the expected answer is {expected_answer}. Try again!"

    def generate_solution_steps(
        self,
        equation: str,
        variable: str = 'x'
    ) -> Dict[str, Any]:
        """Generate step-by-step solution for an equation.

        Args:
            equation: Equation to solve (e.g., "x^2 - 4 = 0")
            variable: Variable to solve for

        Returns:
            Dictionary with solutions and steps
        """
        try:
            # Parse the equation
            parse_result = self.sympy_service.parse_expression(equation)
            if not parse_result['success']:
                return {
                    'solvable': False,
                    'error': parse_result['error'],
                    'steps': []
                }

            expr = parse_result['result']

            # Get the variable symbol
            var = symbols(variable)

            # Solve the equation
            solutions = solve(expr, var)

            if not solutions:
                return {
                    'solvable': False,
                    'error': 'No solution found',
                    'steps': []
                }

            # Generate steps
            steps = []

            # Try to factor
            factor_result = self.sympy_service.factor_expression(equation)
            if factor_result['success'] and factor_result['result'] != equation:
                steps.append(f"Factor: {factor_result['result']} = 0")

            # Add solutions
            if len(solutions) == 1:
                steps.append(f"Solution: {variable} = {solutions[0]}")
            else:
                solution_strs = [f"{variable} = {sol}" for sol in solutions]
                steps.append(f"Solutions: {' or '.join(solution_strs)}")

            return {
                'solvable': True,
                'solutions': [str(sol) for sol in solutions],
                'steps': steps
            }

        except Exception as e:
            logger.error(f"Error generating solution steps: {e}")
            return {
                'solvable': False,
                'error': str(e),
                'steps': []
            }

    def validate_multiple_forms(
        self,
        student_answer: str,
        valid_forms: List[str]
    ) -> Dict[str, Any]:
        """Check if student answer matches any of multiple valid forms.

        Args:
            student_answer: Student's answer
            valid_forms: List of equivalent valid answer forms

        Returns:
            Validation response
        """
        for expected in valid_forms:
            result = self.validate_answer(student_answer, expected)
            if result['correct']:
                return result

        # None matched
        return {
            'correct': False,
            'student_answer': student_answer,
            'expected_answer': ' or '.join(valid_forms),
            'explanation': f"Not quite. The answer should be one of: {', '.join(valid_forms)}"
        }
