"""Integration test for SymPy integration in conversation flow."""
import sys
sys.path.insert(0, '/Users/joaocarlinho/gauntlet/bmad/supertutors/backend')

from app.services.math_detector import MathDetector
from app.services.sympy_service import SymPyService
from app.services.answer_validator import AnswerValidator

def test_full_integration():
    """Test the complete SymPy integration workflow."""

    print("=" * 70)
    print("SYMPY INTEGRATION TEST")
    print("=" * 70)

    # Initialize services
    math_detector = MathDetector(min_confidence=0.6)
    sympy_service = SymPyService()
    answer_validator = AnswerValidator()

    # Test scenarios
    test_scenarios = [
        {
            'name': 'Simple equation',
            'student_input': 'I think x + 5 = 10',
            'expected_expressions': ['x + 5 = 10']
        },
        {
            'name': 'Answer statement',
            'student_input': 'Is x = 5 the correct answer?',
            'expected_expressions': ['x = 5']
        },
        {
            'name': 'Expression to simplify',
            'student_input': 'Can you help me simplify 2x + 3x?',
            'expected_expressions': ['2x + 3x']
        },
        {
            'name': 'Quadratic equation',
            'student_input': 'How do I solve x^2 - 4 = 0?',
            'expected_expressions': ['x^2 - 4 = 0']
        },
        {
            'name': 'No math',
            'student_input': 'What is algebra?',
            'expected_expressions': []
        }
    ]

    for scenario in test_scenarios:
        print(f"\n{'=' * 70}")
        print(f"TEST: {scenario['name']}")
        print(f"Input: {scenario['student_input']}")
        print("-" * 70)

        # Step 1: Detect math
        detection_result = math_detector.detect(scenario['student_input'])

        print(f"Math detected: {detection_result['has_math']}")
        print(f"Confidence: {detection_result['confidence']:.2f}")

        if not detection_result['has_math']:
            print("✓ No math detected (as expected)" if not scenario['expected_expressions'] else "✗ Math should have been detected!")
            continue

        print(f"Expressions found: {len(detection_result['expressions'])}")

        # Step 2: Extract for SymPy
        expr_strings = math_detector.extract_expressions_for_sympy(detection_result)
        print(f"SymPy expressions: {expr_strings}")

        # Step 3: Process with SymPy
        math_context = {
            'detected': True,
            'confidence': detection_result['confidence'],
            'overall_type': detection_result['overall_type'],
            'expressions': []
        }

        for expr_str in expr_strings[:3]:
            print(f"\nProcessing: '{expr_str}'")

            expr_result = {
                'original': expr_str,
                'parsed': None,
                'simplified': None,
                'type': None,
                'solutions': [],
                'steps': []
            }

            try:
                # Parse
                parse_result = sympy_service.parse_expression(expr_str)
                if parse_result['success']:
                    expr_result['parsed'] = str(parse_result['result'])
                    print(f"  Parsed: {expr_result['parsed']}")

                    # Simplify
                    simplify_result = sympy_service.simplify_expression(expr_str)
                    if simplify_result['success']:
                        expr_result['simplified'] = simplify_result['result']
                        print(f"  Simplified: {expr_result['simplified']}")

                    # If equation, solve
                    if '=' in expr_str:
                        expr_result['type'] = 'equation'
                        solve_result = sympy_service.solve_equation(expr_str)
                        if solve_result['success'] and solve_result['result']['solvable']:
                            expr_result['solutions'] = solve_result['result']['solutions']
                            print(f"  Solutions: {expr_result['solutions']}")

                            # Generate steps
                            steps_result = answer_validator.generate_solution_steps(expr_str)
                            if steps_result.get('solvable'):
                                expr_result['steps'] = steps_result['steps']
                                print(f"  Steps: {expr_result['steps']}")
                    else:
                        expr_result['type'] = 'expression'

                    math_context['expressions'].append(expr_result)
                    print("  ✓ Successfully processed")
                else:
                    print(f"  ✗ Parse failed: {parse_result['error']}")

            except Exception as e:
                print(f"  ✗ Error: {e}")

        print(f"\n✓ Test '{scenario['name']}' completed")

    print("\n" + "=" * 70)
    print("ANSWER VALIDATION TEST")
    print("=" * 70)

    # Test answer validation
    validation_tests = [
        {
            'student': 'x = 5',
            'expected': '5',
            'should_match': True
        },
        {
            'student': '5',
            'expected': 'x = 5',
            'should_match': True
        },
        {
            'student': '2x + 3x',
            'expected': '5x',
            'should_match': True
        },
        {
            'student': 'x^2 - 1',
            'expected': '(x-1)(x+1)',
            'should_match': True
        },
        {
            'student': '7',
            'expected': '5',
            'should_match': False
        }
    ]

    for test in validation_tests:
        print(f"\nValidating: '{test['student']}' vs '{test['expected']}'")
        result = answer_validator.validate_answer(
            student_answer=test['student'],
            expected_answer=test['expected']
        )

        correct = result['correct']
        expected_correct = test['should_match']

        status = "✓" if correct == expected_correct else "✗"
        print(f"  {status} Correct: {correct} (expected: {expected_correct})")
        print(f"  Explanation: {result['explanation']}")

    print("\n" + "=" * 70)
    print("✓ ALL INTEGRATION TESTS COMPLETED")
    print("=" * 70)

if __name__ == "__main__":
    test_full_integration()
