"""SymPy Service - symbolic mathematics computation wrapper."""
import logging
from typing import Dict, Any, Optional, List, Union
import sympy
from sympy import sympify, simplify, factor, expand, solve, diff, integrate, SympifyError, symbols, Eq

logger = logging.getLogger(__name__)


class SymPyService:
    """Service wrapper for SymPy operations with error handling."""

    def __init__(self):
        """Initialize SymPy service."""
        logger.info(f"Initialized SymPy service (version {sympy.__version__})")

    def _standardize_response(
        self,
        success: bool,
        result: Any = None,
        error: Optional[str] = None
    ) -> Dict[str, Any]:
        """Standardize response format.

        Args:
            success: Whether operation succeeded
            result: Result data (if successful)
            error: Error message (if failed)

        Returns:
            Standardized response dictionary
        """
        return {
            'success': success,
            'result': result,
            'error': error
        }

    def parse_expression(self, expr_str: str) -> Dict[str, Any]:
        """Parse mathematical expression string to SymPy expression.

        Args:
            expr_str: Expression string (e.g., "x^2 + 2*x + 1")

        Returns:
            Standardized response with parsed expression or error
        """
        try:
            # Handle common input formats: convert ^ to **
            expr_str = expr_str.replace('^', '**')

            # Parse using sympify
            expr = sympify(expr_str)

            logger.debug(f"Successfully parsed expression: {expr_str}")
            return self._standardize_response(True, result=expr)

        except SympifyError as e:
            error_msg = f"Could not parse expression. Check your syntax: {str(e)}"
            logger.warning(f"Parse error for '{expr_str}': {e}")
            return self._standardize_response(False, error=error_msg)

        except TypeError as e:
            error_msg = f"Invalid expression type: {str(e)}"
            logger.warning(f"Type error for '{expr_str}': {e}")
            return self._standardize_response(False, error=error_msg)

        except Exception as e:
            error_msg = "An unexpected error occurred"
            logger.error(f"Unexpected error parsing '{expr_str}': {e}")
            return self._standardize_response(False, error=error_msg)

    def simplify_expression(self, expr_str: str) -> Dict[str, Any]:
        """Simplify mathematical expression.

        Args:
            expr_str: Expression string

        Returns:
            Standardized response with simplified expression
        """
        try:
            # First parse the expression
            parse_result = self.parse_expression(expr_str)
            if not parse_result['success']:
                return parse_result

            expr = parse_result['result']
            simplified = simplify(expr)

            logger.debug(f"Simplified '{expr_str}' to '{simplified}'")
            return self._standardize_response(True, result=str(simplified))

        except Exception as e:
            error_msg = f"Simplification error: {str(e)}"
            logger.error(f"Error simplifying '{expr_str}': {e}")
            return self._standardize_response(False, error=error_msg)

    def factor_expression(self, expr_str: str) -> Dict[str, Any]:
        """Factor mathematical expression.

        Args:
            expr_str: Expression string

        Returns:
            Standardized response with factored expression
        """
        try:
            parse_result = self.parse_expression(expr_str)
            if not parse_result['success']:
                return parse_result

            expr = parse_result['result']
            factored = factor(expr)

            logger.debug(f"Factored '{expr_str}' to '{factored}'")
            return self._standardize_response(True, result=str(factored))

        except Exception as e:
            error_msg = f"Factoring error: {str(e)}"
            logger.error(f"Error factoring '{expr_str}': {e}")
            return self._standardize_response(False, error=error_msg)

    def expand_expression(self, expr_str: str) -> Dict[str, Any]:
        """Expand mathematical expression.

        Args:
            expr_str: Expression string

        Returns:
            Standardized response with expanded expression
        """
        try:
            parse_result = self.parse_expression(expr_str)
            if not parse_result['success']:
                return parse_result

            expr = parse_result['result']
            expanded = expand(expr)

            logger.debug(f"Expanded '{expr_str}' to '{expanded}'")
            return self._standardize_response(True, result=str(expanded))

        except Exception as e:
            error_msg = f"Expansion error: {str(e)}"
            logger.error(f"Error expanding '{expr_str}': {e}")
            return self._standardize_response(False, error=error_msg)

    def solve_equation(
        self,
        equation_str: str,
        variable: str = 'x'
    ) -> Dict[str, Any]:
        """Solve an equation for a given variable.

        Args:
            equation_str: Equation string (e.g., "x^2 - 4 = 0" or "x^2 - 4")
            variable: Variable to solve for (default: 'x')

        Returns:
            Standardized response with solutions array
        """
        try:
            # Handle equations with = sign
            if '=' in equation_str:
                left, right = equation_str.split('=', 1)
                left_parse = self.parse_expression(left.strip())
                right_parse = self.parse_expression(right.strip())

                if not left_parse['success']:
                    return left_parse
                if not right_parse['success']:
                    return right_parse

                expr = left_parse['result'] - right_parse['result']
            else:
                # Assume = 0
                parse_result = self.parse_expression(equation_str)
                if not parse_result['success']:
                    return parse_result
                expr = parse_result['result']

            # Get the variable symbol
            var = symbols(variable)

            # Solve
            solutions = solve(expr, var)

            if not solutions:
                return self._standardize_response(
                    True,
                    result={
                        'solvable': False,
                        'solutions': [],
                        'message': 'No solution found'
                    }
                )

            # Handle special case: infinite solutions
            if solutions == [True]:
                return self._standardize_response(
                    True,
                    result={
                        'solvable': False,
                        'solutions': [],
                        'message': 'Infinite solutions (identity)'
                    }
                )

            solution_strs = [str(sol) for sol in solutions]

            logger.debug(f"Solved '{equation_str}' for {variable}: {solution_strs}")
            return self._standardize_response(
                True,
                result={
                    'solvable': True,
                    'solutions': solution_strs,
                    'count': len(solution_strs)
                }
            )

        except Exception as e:
            error_msg = f"Error solving equation: {str(e)}"
            logger.error(f"Error solving '{equation_str}': {e}")
            return self._standardize_response(False, error=error_msg)

    def differentiate(
        self,
        expr_str: str,
        variable: str = 'x'
    ) -> Dict[str, Any]:
        """Differentiate an expression with respect to a variable.

        Args:
            expr_str: Expression string
            variable: Variable to differentiate with respect to

        Returns:
            Standardized response with derivative
        """
        try:
            parse_result = self.parse_expression(expr_str)
            if not parse_result['success']:
                return parse_result

            expr = parse_result['result']
            var = symbols(variable)

            derivative = diff(expr, var)

            logger.debug(f"Differentiated '{expr_str}' w.r.t. {variable}: {derivative}")
            return self._standardize_response(True, result=str(derivative))

        except Exception as e:
            error_msg = f"Differentiation error: {str(e)}"
            logger.error(f"Error differentiating '{expr_str}': {e}")
            return self._standardize_response(False, error=error_msg)

    def integrate_expression(
        self,
        expr_str: str,
        variable: str = 'x'
    ) -> Dict[str, Any]:
        """Integrate an expression with respect to a variable.

        Args:
            expr_str: Expression string
            variable: Variable to integrate with respect to

        Returns:
            Standardized response with integral
        """
        try:
            parse_result = self.parse_expression(expr_str)
            if not parse_result['success']:
                return parse_result

            expr = parse_result['result']
            var = symbols(variable)

            integral = integrate(expr, var)

            logger.debug(f"Integrated '{expr_str}' w.r.t. {variable}: {integral}")
            return self._standardize_response(True, result=str(integral))

        except Exception as e:
            error_msg = f"Integration error: {str(e)}"
            logger.error(f"Error integrating '{expr_str}': {e}")
            return self._standardize_response(False, error=error_msg)

    def health_check(self) -> Dict[str, Any]:
        """Perform health check with sample computation.

        Returns:
            Health check response with status and sample computation
        """
        try:
            # Test parse and simplify
            test_expr = "x**2 + 2*x + 1"
            parse_result = self.parse_expression(test_expr)

            if not parse_result['success']:
                return {
                    'status': 'error',
                    'version': sympy.__version__,
                    'error': 'Health check failed: could not parse test expression'
                }

            expr = parse_result['result']
            factored = factor(expr)

            return {
                'status': 'ok',
                'version': sympy.__version__,
                'sample_computation': f"{test_expr} = {factored}"
            }

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                'status': 'error',
                'version': sympy.__version__,
                'error': str(e)
            }
