"""Standalone test script for LLM service (no Flask dependency)."""
import os
import logging
from typing import Optional, Dict, Any
from functools import wraps
import signal
from contextlib import contextmanager

import ollama


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class LLMTimeoutError(Exception):
    """Raised when LLM request exceeds timeout."""
    pass


@contextmanager
def timeout_handler(seconds: int):
    """Context manager for timeout handling."""
    def _handle_timeout(signum: Any, frame: Any) -> None:
        raise LLMTimeoutError(f"LLM request exceeded {seconds}s timeout")

    old_handler = signal.signal(signal.SIGALRM, _handle_timeout)
    signal.alarm(seconds)

    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)


def test_health_check():
    """Test Ollama health check."""
    print("\n" + "=" * 60)
    print("1. Health Check")
    print("=" * 60)

    try:
        models = ollama.list()
        print(f"✓ Ollama connected successfully")

        # Check if llama3.2:latest is available
        model_name = 'llama3.2:latest'
        model_available = any(
            model.model == model_name
            for model in models.models
        )

        if model_available:
            print(f"✓ Model '{model_name}' is available")
            return True
        else:
            print(f"✗ Model '{model_name}' not found")
            print(f"Available models: {[m.model for m in models.models]}")
            return False

    except Exception as e:
        print(f"✗ Health check failed: {e}")
        return False


def test_socratic_questioning():
    """Test Socratic questioning prompt."""
    print("\n" + "=" * 60)
    print("2. Socratic Questioning")
    print("=" * 60)

    system_prompt = "You are a patient math tutor using the Socratic method. Never give direct answers. Guide students with questions."
    user_prompt = "Student says: Is x = 5 the answer to x + 2 = 7?"

    print(f"\nSystem: {system_prompt}")
    print(f"User: {user_prompt}")
    print("\nGenerating response (this may take 10-20 seconds)...")

    try:
        with timeout_handler(30):
            response = ollama.chat(
                model='llama3.2:latest',
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_prompt}
                ],
                options={'temperature': 0.7}
            )

            completion = response['message']['content']
            print(f"\n✓ Response ({len(completion)} chars):")
            print(f"{completion}")
            return True

    except LLMTimeoutError as e:
        print(f"✗ Timeout: {e}")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_response_validation():
    """Test response validation prompt."""
    print("\n" + "=" * 60)
    print("3. Response Validation")
    print("=" * 60)

    system_prompt = "Analyze if the student's mathematical reasoning is correct. Be brief and clear."
    user_prompt = "Student reasoning: x + 2 = 7, so I subtract 2 from both sides to get x = 5"

    print(f"\nSystem: {system_prompt}")
    print(f"User: {user_prompt}")
    print("\nGenerating response (this may take 10-20 seconds)...")

    try:
        with timeout_handler(30):
            response = ollama.chat(
                model='llama3.2:latest',
                messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_prompt}
                ],
                options={'temperature': 0.3}
            )

            completion = response['message']['content']
            print(f"\n✓ Response ({len(completion)} chars):")
            print(f"{completion}")
            return True

    except LLMTimeoutError as e:
        print(f"✗ Timeout: {e}")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Testing LLM Service (Ollama + Llama 3.2 Vision 11B)")
    print("=" * 60)

    # Test health
    health_ok = test_health_check()
    if not health_ok:
        print("\n⚠ Skipping generation tests due to health check failure")
        return

    # Test prompts
    test_socratic_questioning()
    test_response_validation()

    print("\n" + "=" * 60)
    print("Testing Complete!")
    print("=" * 60)


if __name__ == '__main__':
    main()
