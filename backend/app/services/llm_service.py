"""LLM Service abstraction layer for Ollama integration.

This module provides a service interface for LLM interactions, currently using
Ollama with Llama 3.2 Vision 11B model for Socratic tutoring and response validation.

Example Prompts:
    Socratic Questioning:
        system_prompt = "You are a patient math tutor using the Socratic method. Never give direct answers."
        user_prompt = "Student says: Is x = 5 the answer?"

    Response Validation:
        system_prompt = "Analyze if the student's reasoning is correct."
        user_prompt = "Student reasoning: x + 2 = 7, so x = 5"
"""

import os
import logging
from typing import Optional, Dict, Any
from functools import wraps
import signal
from contextlib import contextmanager

import ollama
from ollama import ChatResponse


# Configure logging
logger = logging.getLogger(__name__)


class LLMServiceError(Exception):
    """Base exception for LLM service errors."""
    pass


class LLMTimeoutError(LLMServiceError):
    """Raised when LLM request exceeds timeout."""
    pass


class LLMNetworkError(LLMServiceError):
    """Raised when Ollama service is unreachable."""
    pass


class LLMRateLimitError(LLMServiceError):
    """Raised when rate limit is exceeded."""
    pass


@contextmanager
def timeout_handler(seconds: int):
    """Context manager for timeout handling.

    Args:
        seconds: Maximum seconds to allow for execution

    Raises:
        LLMTimeoutError: If execution exceeds timeout
    """
    def _handle_timeout(signum: Any, frame: Any) -> None:
        raise LLMTimeoutError(f"LLM request exceeded {seconds}s timeout")

    # Set the signal handler
    old_handler = signal.signal(signal.SIGALRM, _handle_timeout)
    signal.alarm(seconds)

    try:
        yield
    finally:
        # Restore the old signal handler and cancel the alarm
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)


class LLMService:
    """Service abstraction for LLM interactions.

    This class provides a clean interface for generating completions using Ollama,
    with timeout protection, error handling, and optional streaming support.

    Attributes:
        model_name: The Ollama model identifier (default: llama3.2-vision:11b)
        timeout_seconds: Maximum time for each LLM call (default: 10)
        base_url: Ollama server URL (default: http://localhost:11434)
    """

    def __init__(
        self,
        model_name: Optional[str] = None,
        timeout_seconds: int = 10,
        base_url: Optional[str] = None
    ):
        """Initialize LLM service.

        Args:
            model_name: Ollama model name (defaults to OLLAMA_MODEL env var or llama3.2-vision:11b)
            timeout_seconds: Max seconds per LLM call (default: 10)
            base_url: Ollama server URL (defaults to OLLAMA_BASE_URL env var or localhost)
        """
        self.model_name = model_name or os.environ.get('OLLAMA_MODEL', 'llama3.2-vision:11b')
        self.timeout_seconds = timeout_seconds
        self.base_url = base_url or os.environ.get('OLLAMA_BASE_URL', 'http://localhost:11434')

        logger.info(
            f"LLMService initialized: model={self.model_name}, "
            f"timeout={self.timeout_seconds}s, base_url={self.base_url}"
        )

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        stream: bool = False,
        temperature: float = 0.7,
    ) -> str:
        """Generate a completion from the LLM.

        Args:
            prompt: User message/prompt to send to the LLM
            system_prompt: Optional system message for role/context setting
            stream: Whether to stream the response (default: False)
            temperature: Sampling temperature 0.0-1.0 (default: 0.7)

        Returns:
            The generated completion text

        Raises:
            LLMTimeoutError: If request exceeds timeout
            LLMNetworkError: If Ollama service is unreachable
            LLMServiceError: For other LLM-related errors

        Example:
            >>> service = LLMService()
            >>> response = service.generate(
            ...     prompt="Is x = 5 correct?",
            ...     system_prompt="You are a Socratic math tutor."
            ... )
        """
        messages = []

        if system_prompt:
            messages.append({
                'role': 'system',
                'content': system_prompt
            })

        messages.append({
            'role': 'user',
            'content': prompt
        })

        logger.info(f"Generating completion: model={self.model_name}, stream={stream}")
        logger.debug(f"Messages: {messages}")

        try:
            with timeout_handler(self.timeout_seconds):
                response: ChatResponse = ollama.chat(
                    model=self.model_name,
                    messages=messages,
                    stream=stream,
                    options={
                        'temperature': temperature,
                    }
                )

                if stream:
                    # For streaming, concatenate all chunks
                    full_response = ""
                    for chunk in response:  # type: ignore
                        if 'message' in chunk and 'content' in chunk['message']:
                            full_response += chunk['message']['content']
                    return full_response
                else:
                    # Non-streaming response
                    completion = response['message']['content']
                    logger.info(f"Completion generated: {len(completion)} chars")
                    return completion

        except LLMTimeoutError:
            logger.error(f"LLM request timeout after {self.timeout_seconds}s")
            raise

        except (ConnectionError, OSError) as e:
            logger.error(f"Network error connecting to Ollama: {e}")
            raise LLMNetworkError(f"Could not connect to Ollama at {self.base_url}") from e

        except Exception as e:
            # Check for rate limit errors (if applicable)
            if 'rate limit' in str(e).lower():
                logger.error(f"Rate limit exceeded: {e}")
                raise LLMRateLimitError("Rate limit exceeded") from e

            logger.error(f"Unexpected LLM error: {e}")
            raise LLMServiceError(f"LLM generation failed: {e}") from e

    def check_health(self) -> Dict[str, Any]:
        """Check if Ollama service is healthy and model is available.

        Returns:
            Dict with health status information

        Example:
            >>> service = LLMService()
            >>> health = service.check_health()
            >>> health['status']
            'healthy'
        """
        try:
            # Try to list models to verify Ollama is running
            models = ollama.list()

            # Check if our model is available
            model_available = any(
                model.model == self.model_name
                for model in models.models
            )

            if model_available:
                return {
                    'status': 'healthy',
                    'ollama': 'connected',
                    'model': self.model_name,
                    'model_available': True,
                }
            else:
                return {
                    'status': 'degraded',
                    'ollama': 'connected',
                    'model': self.model_name,
                    'model_available': False,
                    'error': f'Model {self.model_name} not found',
                }

        except (ConnectionError, OSError) as e:
            logger.error(f"Health check failed: Ollama not reachable - {e}")
            return {
                'status': 'unhealthy',
                'ollama': 'disconnected',
                'model': self.model_name,
                'error': str(e),
            }

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                'status': 'unhealthy',
                'ollama': 'unknown',
                'model': self.model_name,
                'error': str(e),
            }


# Singleton instance for application-wide use
_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    """Get the singleton LLM service instance.

    Returns:
        The global LLMService instance
    """
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
