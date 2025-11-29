"""AWS Bedrock Service for Claude 3.5 Sonnet integration.

This module provides a service interface for AWS Bedrock LLM interactions,
specifically for Claude 3.5 Sonnet for Socratic tutoring.
"""

import os
import json
import logging
from typing import Optional, Dict, Any

import boto3
from botocore.exceptions import ClientError, BotoCoreError

logger = logging.getLogger(__name__)


class BedrockServiceError(Exception):
    """Base exception for Bedrock service errors."""
    pass


class BedrockService:
    """Service abstraction for AWS Bedrock interactions with Claude 3.5 Sonnet.

    Attributes:
        model_id: The Bedrock model identifier
        region: AWS region for Bedrock service
        max_tokens: Maximum tokens in response
    """

    def __init__(
        self,
        model_id: Optional[str] = None,
        region: Optional[str] = None,
        max_tokens: int = 2048
    ):
        """Initialize Bedrock service.

        Args:
            model_id: Bedrock model ID (defaults to Claude 3.5 Sonnet)
            region: AWS region (defaults to us-east-1)
            max_tokens: Maximum tokens in response
        """
        self.model_id = model_id or os.environ.get(
            'AWS_BEDROCK_MODEL_ID',
            'anthropic.claude-3-5-sonnet-20241022-v2:0'
        )
        self.region = region or os.environ.get('AWS_REGION', 'us-east-1')
        self.max_tokens = max_tokens

        # Initialize Bedrock client
        self.client = boto3.client(
            service_name='bedrock-runtime',
            region_name=self.region
        )

        logger.info(
            f"BedrockService initialized: model={self.model_id}, "
            f"region={self.region}, max_tokens={self.max_tokens}"
        )

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        top_p: float = 0.9
    ) -> str:
        """Generate a completion from Claude 3.5 Sonnet via Bedrock.

        Args:
            prompt: User message/prompt to send to Claude
            system_prompt: Optional system message for role/context setting
            temperature: Sampling temperature 0.0-1.0 (default: 0.7)
            top_p: Nucleus sampling parameter (default: 0.9)

        Returns:
            The generated completion text

        Raises:
            BedrockServiceError: For Bedrock-related errors
        """
        messages = [{
            'role': 'user',
            'content': prompt
        }]

        # Prepare request body according to Claude's API format
        request_body = {
            'anthropic_version': 'bedrock-2023-05-31',
            'max_tokens': self.max_tokens,
            'temperature': temperature,
            'top_p': top_p,
            'messages': messages
        }

        # Add system prompt if provided
        if system_prompt:
            request_body['system'] = system_prompt

        logger.info(f"Generating completion: model={self.model_id}")
        logger.debug(f"Request: {json.dumps(request_body, indent=2)}")

        try:
            # Invoke Bedrock model
            response = self.client.invoke_model(
                modelId=self.model_id,
                contentType='application/json',
                accept='application/json',
                body=json.dumps(request_body)
            )

            # Parse response
            response_body = json.loads(response['body'].read())

            # Extract completion from Claude's response format
            content = response_body.get('content', [])
            if content and len(content) > 0:
                completion = content[0].get('text', '')
                logger.info(f"Completion generated: {len(completion)} chars")
                return completion
            else:
                raise BedrockServiceError("Empty response from Bedrock")

        except ClientError as e:
            error_code = e.response['Error']['Code']
            error_message = e.response['Error']['Message']
            logger.error(f"Bedrock ClientError: {error_code} - {error_message}")

            if error_code == 'ThrottlingException':
                raise BedrockServiceError("Rate limit exceeded") from e
            elif error_code == 'AccessDeniedException':
                raise BedrockServiceError("Access denied to Bedrock model") from e
            else:
                raise BedrockServiceError(f"Bedrock error: {error_message}") from e

        except BotoCoreError as e:
            logger.error(f"BotoCoreError: {e}")
            raise BedrockServiceError(f"AWS service error: {e}") from e

        except Exception as e:
            logger.error(f"Unexpected Bedrock error: {e}")
            raise BedrockServiceError(f"Bedrock generation failed: {e}") from e

    def check_health(self) -> Dict[str, Any]:
        """Check if Bedrock service is accessible.

        Returns:
            Dict with health status information
        """
        try:
            # Try a minimal invocation to test connectivity
            test_body = {
                'anthropic_version': 'bedrock-2023-05-31',
                'max_tokens': 10,
                'messages': [{
                    'role': 'user',
                    'content': 'Hi'
                }]
            }

            response = self.client.invoke_model(
                modelId=self.model_id,
                contentType='application/json',
                accept='application/json',
                body=json.dumps(test_body)
            )

            return {
                'status': 'healthy',
                'service': 'bedrock',
                'model': self.model_id,
                'region': self.region
            }

        except ClientError as e:
            error_code = e.response['Error']['Code']
            logger.error(f"Health check failed: {error_code}")
            return {
                'status': 'unhealthy',
                'service': 'bedrock',
                'model': self.model_id,
                'error': error_code
            }

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                'status': 'unhealthy',
                'service': 'bedrock',
                'error': str(e)
            }


# Singleton instance
_bedrock_service: Optional[BedrockService] = None


def get_bedrock_service() -> BedrockService:
    """Get the singleton Bedrock service instance.

    Returns:
        The global BedrockService instance
    """
    global _bedrock_service
    if _bedrock_service is None:
        _bedrock_service = BedrockService()
    return _bedrock_service
