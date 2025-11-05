"""Test script for LLM service."""
import sys
import os

# Add app directory to path
sys.path.insert(0, os.path.dirname(__file__))

from app.services.llm_service import LLMService


def main():
    """Test the LLM service with example prompts."""
    print("=" * 60)
    print("Testing LLM Service")
    print("=" * 60)

    # Initialize service
    service = LLMService()
    print(f"\nInitialized LLMService:")
    print(f"  Model: {service.model_name}")
    print(f"  Timeout: {service.timeout_seconds}s")
    print(f"  Base URL: {service.base_url}")

    # Test health check
    print("\n" + "-" * 60)
    print("1. Health Check")
    print("-" * 60)
    health = service.check_health()
    print(f"Status: {health['status']}")
    print(f"Ollama: {health.get('ollama', 'unknown')}")
    print(f"Model: {health.get('model', 'unknown')}")
    print(f"Model Available: {health.get('model_available', False)}")
    if 'error' in health:
        print(f"Error: {health['error']}")
        print("\nSkipping generation tests due to health check failure")
        return

    # Test Socratic questioning
    print("\n" + "-" * 60)
    print("2. Socratic Questioning")
    print("-" * 60)
    system_prompt = "You are a patient math tutor using the Socratic method. Never give direct answers. Guide students with questions."
    user_prompt = "Student says: Is x = 5 the answer to x + 2 = 7?"

    print(f"System: {system_prompt}")
    print(f"User: {user_prompt}")
    print("\nGenerating response...")

    try:
        response = service.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.7
        )
        print(f"\nResponse ({len(response)} chars):")
        print(f"{response}")
    except Exception as e:
        print(f"Error: {e}")

    # Test response validation
    print("\n" + "-" * 60)
    print("3. Response Validation")
    print("-" * 60)
    system_prompt = "Analyze if the student's mathematical reasoning is correct. Be brief and clear."
    user_prompt = "Student reasoning: x + 2 = 7, so I subtract 2 from both sides to get x = 5"

    print(f"System: {system_prompt}")
    print(f"User: {user_prompt}")
    print("\nGenerating response...")

    try:
        response = service.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.3  # Lower temperature for more focused analysis
        )
        print(f"\nResponse ({len(response)} chars):")
        print(f"{response}")
    except Exception as e:
        print(f"Error: {e}")

    print("\n" + "=" * 60)
    print("Testing Complete!")
    print("=" * 60)


if __name__ == '__main__':
    main()
