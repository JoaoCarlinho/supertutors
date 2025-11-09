"""Math Expression Detector - identifies mathematical expressions in text."""
import logging
import re
from typing import Dict, List, Any, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class ExpressionType(Enum):
    """Types of mathematical expressions that can be detected."""
    EQUATION = "equation"  # x + 5 = 10
    EXPRESSION = "expression"  # 2x + 3x
    NUMERICAL = "numerical"  # 5 + 3 * 2
    ANSWER_STATEMENT = "answer_statement"  # x = 5
    INEQUALITY = "inequality"  # x > 5
    UNKNOWN = "unknown"


class MathDetector:
    """Service for detecting mathematical expressions in student messages."""

    # Detection patterns with confidence scores
    PATTERNS = [
        # Answer statements (x = 5, y = -3.5) - HIGH confidence
        {
            'name': 'answer_statement',
            'regex': r'\b([a-zA-Z])\s*=\s*([-]?\d+(?:\.\d+)?)\b',
            'type': ExpressionType.ANSWER_STATEMENT,
            'confidence': 0.95
        },
        # Equations with = sign (x + 5 = 10) - HIGH confidence
        # Match patterns like: single_letter/digit then operations then = then right side
        {
            'name': 'equation',
            'regex': r'(?:^|(?<=\s))(?:\d+[\da-zA-Z\+\-\*/\^\(\)\.]*?|[a-z](?:[\d\+\-\*/\^\(\)\.\s])*?)\s*=\s*[\da-zA-Z\+\-\*/\^\(\)\.\s]+?(?=\s*(?:$|[,\.\?!]|and|or|but))',
            'type': ExpressionType.EQUATION,
            'confidence': 0.90,
            'exclude_answer_statement': True  # Don't match simple answer statements
        },
        # Inequalities (x > 5, 2x < 10)
        {
            'name': 'inequality',
            'regex': r'(?:^|(?<=\s))[\d\(a-zA-Z][\da-zA-Z\s\+\-\*/\^\(\)\.]*?\s*[<>≤≥]\s*[\da-zA-Z\s\+\-\*/\^\(\)\.]+?(?=\s|$|[,\.\?!])',
            'type': ExpressionType.INEQUALITY,
            'confidence': 0.85
        },
        # Algebraic expressions with variables (2x + 3, x^2 - 4)
        {
            'name': 'algebraic_expression',
            'regex': r'\b\d*[a-zA-Z][\^\*]?\d*\s*[\+\-]\s*\d*[a-zA-Z]?[\^\*]?\d*',
            'type': ExpressionType.EXPRESSION,
            'confidence': 0.80
        },
        # Products and powers (x^2, 2x, (x+1))
        {
            'name': 'algebraic_term',
            'regex': r'\d*[a-zA-Z][\^\*]\d+|\d+[a-zA-Z]|\([a-zA-Z\s\+\-\d]+\)',
            'type': ExpressionType.EXPRESSION,
            'confidence': 0.75
        },
        # Numerical calculations (5 + 3, 10 * 2)
        {
            'name': 'numerical',
            'regex': r'\b\d+(?:\.\d+)?\s*[\+\-\*/\^]\s*\d+(?:\.\d+)?\b',
            'type': ExpressionType.NUMERICAL,
            'confidence': 0.70
        },
        # Functions (sqrt(16), sin(x))
        {
            'name': 'function',
            'regex': r'\b(sqrt|sin|cos|tan|log|ln|abs)\s*\([^)]+\)',
            'type': ExpressionType.EXPRESSION,
            'confidence': 0.85
        },
        # Fractions (1/2, 3/4)
        {
            'name': 'fraction',
            'regex': r'\b\d+\s*/\s*\d+\b',
            'type': ExpressionType.NUMERICAL,
            'confidence': 0.65
        }
    ]

    # Keywords that increase confidence of math detection
    MATH_KEYWORDS = [
        'solve', 'simplify', 'factor', 'expand', 'equation', 'expression',
        'calculate', 'compute', 'evaluate', 'answer', 'solution', 'equal',
        'plus', 'minus', 'times', 'divided', 'multiply', 'subtract', 'add'
    ]

    # Keywords that decrease confidence (false positives)
    NON_MATH_KEYWORDS = [
        'email', 'address', 'password', 'username', 'code', 'id',
        'phone', 'zip', 'date', 'time', 'version'
    ]

    def __init__(self, min_confidence: float = 0.6):
        """Initialize math detector.

        Args:
            min_confidence: Minimum confidence threshold (0.0-1.0) to consider math detected
        """
        self.min_confidence = min_confidence
        logger.info(f"Initialized MathDetector with min_confidence={min_confidence}")

    def detect(self, text: str) -> Dict[str, Any]:
        """Detect mathematical expressions in text.

        Args:
            text: Student message text to analyze

        Returns:
            Detection result dictionary:
            {
                'has_math': bool,
                'confidence': float (0.0-1.0),
                'expressions': List[Dict],
                'overall_type': ExpressionType,
                'detected_patterns': List[str]
            }
        """
        if not text or not isinstance(text, str):
            return self._empty_result()

        detected_expressions = []
        detected_patterns = []
        max_confidence = 0.0

        # Check each pattern
        for pattern_def in self.PATTERNS:
            matches = re.finditer(pattern_def['regex'], text, re.IGNORECASE)

            for match in matches:
                matched_text = match.group(0).strip()

                # Skip if empty or too short
                if len(matched_text) < 2:
                    continue

                # Special handling for equations to exclude simple answer statements
                if pattern_def.get('exclude_answer_statement'):
                    # If it looks like "x = 5" (simple answer), skip this pattern
                    if re.match(r'^\s*[a-zA-Z]\s*=\s*[-]?\d+(?:\.\d+)?\s*$', matched_text):
                        continue

                confidence = pattern_def['confidence']

                # Adjust confidence based on context
                confidence = self._adjust_confidence(text, matched_text, confidence)

                if confidence >= self.min_confidence:
                    detected_expressions.append({
                        'text': matched_text,
                        'type': pattern_def['type'].value,
                        'pattern_name': pattern_def['name'],
                        'confidence': confidence,
                        'start': match.start(),
                        'end': match.end()
                    })

                    detected_patterns.append(pattern_def['name'])
                    max_confidence = max(max_confidence, confidence)

        # Remove duplicate expressions (keep highest confidence)
        detected_expressions = self._deduplicate_expressions(detected_expressions)

        # Determine overall type (most common or highest confidence)
        overall_type = self._determine_overall_type(detected_expressions)

        has_math = len(detected_expressions) > 0 and max_confidence >= self.min_confidence

        result = {
            'has_math': has_math,
            'confidence': max_confidence,
            'expressions': detected_expressions,
            'overall_type': overall_type.value if overall_type else None,
            'detected_patterns': list(set(detected_patterns)),
            'text_length': len(text)
        }

        if has_math:
            logger.debug(
                f"Math detected: {len(detected_expressions)} expressions, "
                f"confidence={max_confidence:.2f}, type={overall_type.value if overall_type else 'unknown'}"
            )

        return result

    def _adjust_confidence(self, full_text: str, matched_text: str, base_confidence: float) -> float:
        """Adjust confidence based on context.

        Args:
            full_text: Full message text
            matched_text: The matched expression
            base_confidence: Base confidence from pattern

        Returns:
            Adjusted confidence (0.0-1.0)
        """
        confidence = base_confidence
        full_text_lower = full_text.lower()

        # Increase confidence if math keywords present
        math_keyword_count = sum(1 for keyword in self.MATH_KEYWORDS if keyword in full_text_lower)
        if math_keyword_count > 0:
            confidence = min(1.0, confidence + (math_keyword_count * 0.05))

        # Decrease confidence if non-math keywords present
        non_math_keyword_count = sum(1 for keyword in self.NON_MATH_KEYWORDS if keyword in full_text_lower)
        if non_math_keyword_count > 0:
            confidence = max(0.0, confidence - (non_math_keyword_count * 0.1))

        # Decrease confidence if matched text is very short relative to full text
        if len(matched_text) < 3 and len(full_text) > 50:
            confidence = max(0.0, confidence - 0.2)

        return confidence

    def _deduplicate_expressions(self, expressions: List[Dict]) -> List[Dict]:
        """Remove overlapping or duplicate expressions, keeping highest confidence.

        Args:
            expressions: List of detected expressions

        Returns:
            Deduplicated list
        """
        if len(expressions) <= 1:
            return expressions

        # Sort by confidence (descending) then by start position
        sorted_exprs = sorted(
            expressions,
            key=lambda x: (-x['confidence'], x['start'])
        )

        deduplicated = []
        used_ranges = []

        for expr in sorted_exprs:
            expr_range = range(expr['start'], expr['end'])

            # Check if this range overlaps with any used range
            overlaps = any(
                any(pos in used_range for pos in expr_range)
                for used_range in used_ranges
            )

            if not overlaps:
                deduplicated.append(expr)
                used_ranges.append(expr_range)

        # Sort by original position
        deduplicated.sort(key=lambda x: x['start'])

        return deduplicated

    def _determine_overall_type(self, expressions: List[Dict]) -> Optional[ExpressionType]:
        """Determine the overall expression type from detected expressions.

        Args:
            expressions: List of detected expressions

        Returns:
            Overall ExpressionType or None
        """
        if not expressions:
            return None

        # Use the type of the highest confidence expression
        highest_confidence_expr = max(expressions, key=lambda x: x['confidence'])

        try:
            return ExpressionType(highest_confidence_expr['type'])
        except (KeyError, ValueError):
            return ExpressionType.UNKNOWN

    def _empty_result(self) -> Dict[str, Any]:
        """Return empty detection result.

        Returns:
            Empty result dictionary
        """
        return {
            'has_math': False,
            'confidence': 0.0,
            'expressions': [],
            'overall_type': None,
            'detected_patterns': [],
            'text_length': 0
        }

    def extract_expressions_for_sympy(self, detection_result: Dict[str, Any]) -> List[str]:
        """Extract expression strings suitable for SymPy processing.

        Args:
            detection_result: Result from detect() method

        Returns:
            List of expression strings to pass to SymPy
        """
        if not detection_result.get('has_math'):
            return []

        expressions = []
        for expr_info in detection_result.get('expressions', []):
            text = expr_info['text']
            expr_type = expr_info['type']

            # For equations, we might want to rearrange to expression = 0 form
            if expr_type == 'equation' or expr_type == 'answer_statement':
                expressions.append(text)
            elif expr_type in ['expression', 'numerical']:
                expressions.append(text)
            # For inequalities, SymPy can handle them too
            elif expr_type == 'inequality':
                expressions.append(text)

        return expressions
