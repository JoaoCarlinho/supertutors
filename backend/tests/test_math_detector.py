"""Unit tests for Math Expression Detector."""
import pytest
from app.services.math_detector import MathDetector, ExpressionType


class TestMathDetector:
    """Test suite for MathDetector service."""

    def setup_method(self):
        """Set up test fixtures."""
        self.detector = MathDetector(min_confidence=0.6)

    def test_simple_equation(self):
        """Test detection of simple equation."""
        result = self.detector.detect("x + 5 = 10")
        assert result['has_math'] is True
        assert result['confidence'] >= 0.8
        assert len(result['expressions']) >= 1
        assert result['overall_type'] == ExpressionType.EQUATION.value

    def test_quadratic_equation(self):
        """Test detection of quadratic equation."""
        result = self.detector.detect("x^2 - 4 = 0")
        assert result['has_math'] is True
        assert result['overall_type'] in [ExpressionType.EQUATION.value, ExpressionType.EXPRESSION.value]

    def test_answer_statement(self):
        """Test detection of answer statement."""
        result = self.detector.detect("x = 5")
        assert result['has_math'] is True
        assert result['confidence'] >= 0.9
        assert result['overall_type'] == ExpressionType.ANSWER_STATEMENT.value

    def test_negative_answer(self):
        """Test detection of negative answer."""
        result = self.detector.detect("y = -3")
        assert result['has_math'] is True
        assert result['overall_type'] == ExpressionType.ANSWER_STATEMENT.value

    def test_decimal_answer(self):
        """Test detection of decimal answer."""
        result = self.detector.detect("r = 2.5")
        assert result['has_math'] is True
        assert result['overall_type'] == ExpressionType.ANSWER_STATEMENT.value

    def test_algebraic_expression(self):
        """Test detection of algebraic expression."""
        result = self.detector.detect("2x + 3x")
        assert result['has_math'] is True
        assert result['overall_type'] == ExpressionType.EXPRESSION.value

    def test_factored_expression(self):
        """Test detection of factored expression."""
        result = self.detector.detect("(x-1)(x+1)")
        assert result['has_math'] is True

    def test_numerical_calculation(self):
        """Test detection of numerical calculation."""
        result = self.detector.detect("5 + 3")
        assert result['has_math'] is True
        assert result['overall_type'] == ExpressionType.NUMERICAL.value

    def test_numerical_with_operations(self):
        """Test detection of complex numerical calculation."""
        result = self.detector.detect("5 + 3 * 2")
        assert result['has_math'] is True

    def test_fraction(self):
        """Test detection of fraction."""
        result = self.detector.detect("1/2")
        assert result['has_math'] is True
        assert result['overall_type'] == ExpressionType.NUMERICAL.value

    def test_sqrt_function(self):
        """Test detection of square root function."""
        result = self.detector.detect("sqrt(16)")
        assert result['has_math'] is True
        assert result['overall_type'] == ExpressionType.EXPRESSION.value

    def test_inequality(self):
        """Test detection of inequality."""
        result = self.detector.detect("x > 5")
        assert result['has_math'] is True
        assert result['overall_type'] == ExpressionType.INEQUALITY.value

    def test_complex_equation_in_sentence(self):
        """Test detection within natural language."""
        result = self.detector.detect("I think the equation x + 5 = 10 means x = 5")
        assert result['has_math'] is True
        assert len(result['expressions']) >= 1

    def test_multiple_expressions(self):
        """Test detection of multiple expressions."""
        result = self.detector.detect("First solve x + 5 = 10, then calculate 2 + 3")
        assert result['has_math'] is True
        assert len(result['expressions']) >= 2

    def test_no_math_plain_text(self):
        """Test that plain text is not detected as math."""
        result = self.detector.detect("Hello, how are you?")
        assert result['has_math'] is False

    def test_no_math_question(self):
        """Test that questions without math are not detected."""
        result = self.detector.detect("What is algebra?")
        assert result['has_math'] is False

    def test_no_math_empty_string(self):
        """Test that empty string returns no math."""
        result = self.detector.detect("")
        assert result['has_math'] is False

    def test_no_math_none(self):
        """Test that None input returns no math."""
        result = self.detector.detect(None)
        assert result['has_math'] is False

    def test_false_positive_email(self):
        """Test that email addresses are not detected as math."""
        # Note: Simple emails like "user@domain.com" shouldn't trigger
        # But "x = 5" in "email x = user@domain.com" might
        result = self.detector.detect("My email is user@domain.com")
        # Should have low confidence or no detection
        if result['has_math']:
            assert result['confidence'] < 0.7

    def test_math_keyword_boost(self):
        """Test that math keywords increase confidence."""
        result1 = self.detector.detect("x + 5")
        result2 = self.detector.detect("solve x + 5")
        # Result2 should have higher confidence due to 'solve' keyword
        if result1['has_math'] and result2['has_math']:
            assert result2['confidence'] >= result1['confidence']

    def test_extract_expressions_for_sympy(self):
        """Test extraction of expressions for SymPy processing."""
        result = self.detector.detect("x + 5 = 10 and 2x = 6")
        expressions = self.detector.extract_expressions_for_sympy(result)
        assert len(expressions) >= 1
        assert isinstance(expressions[0], str)

    def test_extract_no_math(self):
        """Test extraction when no math detected."""
        result = self.detector.detect("Hello world")
        expressions = self.detector.extract_expressions_for_sympy(result)
        assert len(expressions) == 0

    def test_confidence_threshold(self):
        """Test that low confidence expressions are filtered."""
        detector_strict = MathDetector(min_confidence=0.9)
        result = detector_strict.detect("maybe x?")
        # Should have no detection due to high threshold
        assert result['has_math'] is False or result['confidence'] >= 0.9

    def test_deduplication(self):
        """Test that overlapping expressions are deduplicated."""
        # This text might match multiple patterns for the same expression
        result = self.detector.detect("x + 5 = 10")
        # Should not have duplicate overlapping expressions
        for i, expr1 in enumerate(result['expressions']):
            for expr2 in result['expressions'][i+1:]:
                # Check ranges don't overlap
                range1 = range(expr1['start'], expr1['end'])
                range2 = range(expr2['start'], expr2['end'])
                assert not any(pos in range2 for pos in range1)

    def test_power_notation(self):
        """Test detection of power notation."""
        result = self.detector.detect("x^2")
        assert result['has_math'] is True

    def test_polynomial(self):
        """Test detection of polynomial."""
        result = self.detector.detect("x^2 + 2x + 1")
        assert result['has_math'] is True

    def test_system_of_equations(self):
        """Test detection in system of equations context."""
        result = self.detector.detect("x + y = 5 and x - y = 1")
        assert result['has_math'] is True
        assert len(result['expressions']) >= 2
