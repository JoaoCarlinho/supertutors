"""Vision AI Service - OCR extraction using Llama 3.2 Vision via Ollama."""
import logging
import os
import re
from typing import Dict, Any
from ollama import Client

logger = logging.getLogger(__name__)

OCR_PROMPT = """You are an OCR system specialized in extracting mathematical content.

Analyze this image and extract:
1. All text content (preserve structure and formatting)
2. All mathematical expressions (convert to LaTeX when possible using $ delimiters)
3. Equations, formulas, and diagrams

If the image contains handwritten content, do your best to interpret it accurately.
If you find mathematical notation, wrap it in $ for inline math or $$ for display math.

Return only the extracted content, formatted clearly."""


class VisionService:
    """Service for Vision AI OCR using Llama 3.2 Vision."""

    def __init__(self, model_name: str = "llama3.2-vision:11b"):
        """Initialize Vision service.

        Args:
            model_name: Ollama vision model name
        """
        self.model_name = model_name
        base_url = os.environ.get('OLLAMA_BASE_URL', 'http://localhost:11434')
        self.client = Client(host=base_url)
        logger.info(f"Initialized Vision service with model {model_name}")

    def extract_text_from_image(self, image_path: str) -> Dict[str, Any]:
        """Extract text and math from image using Vision AI.

        Args:
            image_path: Path to image file

        Returns:
            Dictionary with success, extracted_text, confidence, math_detected
        """
        try:
            logger.info(f"Extracting text from image: {image_path}")

            # Call Ollama Vision API
            response = self.client.chat(
                model=self.model_name,
                messages=[{
                    'role': 'user',
                    'content': OCR_PROMPT,
                    'images': [image_path]
                }],
                options={'temperature': 0.1}  # Low temperature for consistent OCR
            )

            extracted_text = response['message']['content'].strip()

            # Estimate confidence based on response characteristics
            confidence = self._estimate_confidence(extracted_text)

            # Detect if math content is present
            math_detected = self._detect_math(extracted_text)

            logger.info(
                f"OCR complete. Confidence: {confidence:.2f}, "
                f"Math detected: {math_detected}, "
                f"Text length: {len(extracted_text)}"
            )

            return {
                'success': True,
                'extracted_text': extracted_text,
                'confidence': confidence,
                'math_detected': math_detected
            }

        except ollama.ResponseError as e:
            error_msg = f"Ollama error: {str(e)}"
            logger.error(f"OCR failed: {error_msg}")
            return {
                'success': False,
                'error': "Failed to process image. Please try again.",
                'extracted_text': '',
                'confidence': 0.0,
                'math_detected': False
            }

        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(f"OCR failed: {error_msg}")
            return {
                'success': False,
                'error': "An error occurred during OCR processing.",
                'extracted_text': '',
                'confidence': 0.0,
                'math_detected': False
            }

    def _estimate_confidence(self, extracted_text: str) -> float:
        """Estimate confidence based on extracted text characteristics.

        Args:
            extracted_text: Extracted text from OCR

        Returns:
            Confidence score between 0 and 1
        """
        if not extracted_text or len(extracted_text) < 5:
            return 0.3  # Very low confidence for minimal text

        # Factors that increase confidence:
        # 1. Reasonable text length (20-1000 chars ideal)
        # 2. Presence of complete words
        # 3. Proper capitalization/punctuation
        # 4. Math notation detected

        confidence = 0.5  # Base confidence

        # Length factor
        text_length = len(extracted_text)
        if 20 <= text_length <= 1000:
            confidence += 0.2
        elif text_length > 1000:
            confidence += 0.1

        # Word completeness (no excessive fragmentation)
        words = extracted_text.split()
        avg_word_length = sum(len(w) for w in words) / max(len(words), 1)
        if avg_word_length >= 4:
            confidence += 0.1

        # Punctuation/structure
        if any(char in extracted_text for char in ['.', ',', '?', '!']):
            confidence += 0.1

        # Math notation
        if self._detect_math(extracted_text):
            confidence += 0.1

        return min(confidence, 1.0)

    def _detect_math(self, text: str) -> bool:
        """Detect if text contains mathematical content.

        Args:
            text: Text to analyze

        Returns:
            True if math content detected
        """
        # Check for LaTeX delimiters
        if '$' in text or '\\frac' in text or '\\sqrt' in text:
            return True

        # Check for mathematical symbols
        math_symbols = ['×', '÷', '±', '≠', '≤', '≥', '√', 'π', '∫', '∑', '∞', '=']
        if any(symbol in text for symbol in math_symbols):
            return True

        # Check for equations (variables with operators)
        equation_pattern = r'[a-zA-Z]\s*[+\-*/=]\s*\d+'
        if re.search(equation_pattern, text):
            return True

        # Check for numbers with operators
        if re.search(r'\d+\s*[+\-*/=]\s*\d+', text):
            return True

        return False

    def check_model_availability(self) -> Dict[str, Any]:
        """Check if Vision model is available.

        Returns:
            Dictionary with status and model info
        """
        try:
            models = ollama.list()
            model_names = [model['name'] for model in models.get('models', [])]

            available = any(self.model_name in name for name in model_names)

            return {
                'available': available,
                'model': self.model_name,
                'installed_models': model_names
            }

        except Exception as e:
            logger.error(f"Error checking model availability: {e}")
            return {
                'available': False,
                'model': self.model_name,
                'error': str(e)
            }
