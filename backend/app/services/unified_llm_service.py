"""Unified LLM Service that supports both Ollama (local) and AWS Bedrock (cloud).

This module provides a unified interface that automatically selects between
Ollama and Bedrock based on environment configuration.
"""

import os
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class UnifiedLLMService:
    """Unified LLM service that routes to Ollama or Bedrock based on configuration."""

    def __init__(self):
        """Initialize the unified LLM service."""
        self.use_bedrock = os.environ.get('USE_AWS_BEDROCK', 'false').lower() == 'true'

        if self.use_bedrock:
            logger.info("Initializing AWS Bedrock service")
            from app.services.bedrock_service import get_bedrock_service
            self.service = get_bedrock_service()
            self.service_name = "Bedrock"
        else:
            logger.info("Initializing Ollama service")
            from app.services.llm_service import get_llm_service
            self.service = get_llm_service()
            self.service_name = "Ollama"

        logger.info(f"UnifiedLLMService initialized with: {self.service_name}")

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """Generate a completion using the configured LLM service.

        Args:
            prompt: User message/prompt
            system_prompt: Optional system message
            temperature: Sampling temperature
            **kwargs: Additional service-specific parameters

        Returns:
            The generated completion text
        """
        logger.debug(f"Generating with {self.service_name}: prompt_length={len(prompt)}")

        return self.service.generate(
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            **kwargs
        )

    def check_health(self) -> Dict[str, Any]:
        """Check health of the configured LLM service.

        Returns:
            Dict with health status information
        """
        health = self.service.check_health()
        health['service_name'] = self.service_name
        health['use_bedrock'] = self.use_bedrock
        return health


# Singleton instance
_unified_llm_service: Optional[UnifiedLLMService] = None


def get_unified_llm_service() -> UnifiedLLMService:
    """Get the singleton unified LLM service instance.

    Returns:
        The global UnifiedLLMService instance
    """
    global _unified_llm_service
    if _unified_llm_service is None:
        _unified_llm_service = UnifiedLLMService()
    return _unified_llm_service
