"""Vision AI Service - OCR extraction using OpenAI GPT-4 Vision."""
import logging
import os
import re
import base64
from typing import Dict, Any
from openai import OpenAI

logger = logging.getLogger(__name__)

OCR_PROMPT = """You are a vision AI that MUST read EXACTLY what is written in the image. Your job is OCR (Optical Character Recognition) - reading text, NOT generating math problems.

⚠️ CRITICAL WARNING ⚠️
DO NOT generate random equations. DO NOT make up math problems. DO NOT use examples.
You MUST read ONLY what is actually written in the image, character by character.

**STEP 1: Describe what you see**
Look at the image and describe the mathematical notation character by character from left to right.

**STEP 2: Identify problem type**
- ALGEBRA: has variables (x, y, etc.) and equations
- GEOMETRY: has shapes, diagrams, or geometric figures
- ARITHMETIC: only numbers and basic operations (+, -, ×, ÷)

**STEP 3: Extract EXACTLY what is written**

Read character by character from left to right. For example:
- If you see "3", write "3" (not 5, not 2, not any other number)
- If you see "x", write "x" (not y, not z)
- If you see "+", write "+" (not -, not ×)
- If you see "2", write "2" (not 5, not 7)
- If you see "=", write "=" (exactly as shown)
- If you see "5", write "5" (not 20, not 7)

**STEP 4: Format output**

FOR ALGEBRA (with variables):
Format: "Linear equation: $[exactly what you read]$"

FOR GEOMETRY (shapes):
Format: "[Shape type] with [measurements you see]"

FOR ARITHMETIC (numbers only):
Format: "Arithmetic: $[exactly what you read]$"

⚠️ VERIFICATION CHECK ⚠️
Before responding, ask yourself:
1. Did I read each character from the actual image?
2. Did I make up ANY numbers or variables?
3. Does my answer match EXACTLY what is written?

If you cannot read the handwriting clearly, say "Cannot read clearly" instead of guessing."""


class VisionService:
    """Service for Vision AI OCR using OpenAI GPT-4 Vision."""

    def __init__(self, model_name: str = "gpt-4o"):
        """Initialize Vision service.

        Args:
            model_name: OpenAI vision model name (gpt-4o or gpt-4-vision-preview)
        """
        self.model_name = model_name
        api_key = os.environ.get('OPENAI_API_KEY')

        if not api_key:
            logger.error("OPENAI_API_KEY not found in environment variables")
            raise ValueError("OPENAI_API_KEY is required")

        self.client = OpenAI(api_key=api_key)
        logger.info(f"Initialized Vision service with model {model_name}")

    def extract_text_from_image(self, image_path: str, subject: str = None) -> Dict[str, Any]:
        """Extract text and math from image using Vision AI.

        Args:
            image_path: Path to image file
            subject: Optional subject hint ('algebra', 'geometry', 'arithmetic')

        Returns:
            Dictionary with success, extracted_text, confidence, math_detected
        """
        try:
            logger.info(f"Extracting text from image: {image_path}, subject: {subject}")

            # Encode image as base64
            with open(image_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')

            # Determine image format from file extension
            image_format = image_path.split('.')[-1].lower()
            if image_format == 'jpg':
                image_format = 'jpeg'

            # Build prompt with subject hint if provided
            prompt_text = OCR_PROMPT
            if subject:
                subject_hints = {
                    'algebra': 'The student indicated this is an ALGEBRA problem (equations, expressions, variables). Focus on extracting equations and algebraic expressions.',
                    'geometry': 'The student indicated this is a GEOMETRY problem (shapes, figures, measurements). Focus on identifying geometric shapes and their properties.',
                    'arithmetic': 'The student indicated this is an ARITHMETIC problem (basic calculations). Focus on extracting numbers and operations.'
                }
                hint = subject_hints.get(subject.lower(), '')
                if hint:
                    prompt_text = f"{hint}\n\n{OCR_PROMPT}"

            # Call OpenAI Vision API
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt_text
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/{image_format};base64,{base64_image}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=1000,
                temperature=0.3  # Slightly higher temperature for better handwriting interpretation
            )

            extracted_text = response.choices[0].message.content.strip()

            # Log the actual extracted text for debugging
            logger.info(f"RAW OCR OUTPUT: {extracted_text}")
            logger.info(f"Subject hint used: {subject}")

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

        except Exception as e:
            error_msg = f"OpenAI Vision API error: {str(e)}"
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

        # GPT-4 Vision is generally high quality, start with higher base
        confidence = 0.7  # Base confidence for GPT-4 Vision

        # Length factor
        text_length = len(extracted_text)
        if 20 <= text_length <= 1000:
            confidence += 0.15
        elif text_length > 1000:
            confidence += 0.05

        # Word completeness (no excessive fragmentation)
        words = extracted_text.split()
        avg_word_length = sum(len(w) for w in words) / max(len(words), 1)
        if avg_word_length >= 4:
            confidence += 0.1

        # Math notation (GPT-4 is very good at this)
        if self._detect_math(extracted_text):
            confidence += 0.05

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
        math_symbols = [
            '×', '÷', '±', '≠', '≤', '≥', '√', 'π', '∫', '∑', '∞', '='
        ]
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
        """Check if OpenAI API is available.

        Returns:
            Dictionary with status and model info
        """
        try:
            # Try a simple API call to check availability
            self.client.models.list()

            return {
                'available': True,
                'model': self.model_name,
                'provider': 'OpenAI'
            }

        except Exception as e:
            logger.error(f"Error checking model availability: {e}")
            return {
                'available': False,
                'model': self.model_name,
                'error': str(e)
            }
