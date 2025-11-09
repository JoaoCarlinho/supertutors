"""Manual test script for Math Detector."""
import sys
sys.path.insert(0, '/Users/joaocarlinho/gauntlet/bmad/supertutors/backend')

from app.services.math_detector import MathDetector

def test_math_detector():
    """Run manual tests on math detector."""
    detector = MathDetector(min_confidence=0.6)

    test_cases = [
        ("x + 5 = 10", "Simple equation"),
        ("x = 5", "Answer statement"),
        ("2x + 3x", "Algebraic expression"),
        ("5 + 3", "Numerical"),
        ("sqrt(16)", "Function"),
        ("Hello world", "No math"),
        ("I think x + 5 = 10 means x = 5", "Math in sentence"),
        ("x^2 - 4 = 0", "Quadratic"),
        ("1/2 + 1/4", "Fractions"),
        ("x > 5", "Inequality"),
    ]

    print("=" * 70)
    print("MATH DETECTOR MANUAL TESTS")
    print("=" * 70)

    for text, description in test_cases:
        print(f"\nTest: {description}")
        print(f"Input: '{text}'")

        result = detector.detect(text)

        print(f"Has math: {result['has_math']}")
        print(f"Confidence: {result['confidence']:.2f}")
        print(f"Overall type: {result['overall_type']}")
        print(f"Expressions found: {len(result['expressions'])}")

        for i, expr in enumerate(result['expressions'], 1):
            print(f"  {i}. '{expr['text']}' (type: {expr['type']}, conf: {expr['confidence']:.2f})")

        # Test extraction for SymPy
        sympy_exprs = detector.extract_expressions_for_sympy(result)
        if sympy_exprs:
            print(f"SymPy ready: {sympy_exprs}")

        print("-" * 70)

    print("\n✓ All manual tests completed")

if __name__ == "__main__":
    test_math_detector()
