"""Hybrid OCR Service - Two-stage pipeline using Pix2Text + GPT-4o verification.

Story 8-2: Implement Hybrid OCR Pipeline
- Stage 1: Pix2Text for specialized math OCR extraction (LaTeX output)
- Stage 2: GPT-4o verification for low-confidence results
- Graceful fallback to GPT-4o-only mode if Pix2Text unavailable

Enhanced with:
- Image optimization (resize large images before processing)
- Progress callback support for WebSocket updates
"""
import logging
import os
import base64
import json
import re
from typing import Dict, Any, Optional, Literal, Callable
from dataclasses import dataclass, field
from PIL import Image

logger = logging.getLogger(__name__)

# Try to import Pix2Text - may not be available in all environments
PIX2TEXT_AVAILABLE = False
try:
    from pix2text import Pix2Text
    PIX2TEXT_AVAILABLE = True
    logger.info("Pix2Text imported successfully")
except ImportError as e:
    logger.warning(f"Pix2Text not available: {e}. Will use GPT-4o fallback.")

# Import OpenAI for verification stage
try:
    from openai import OpenAI
except ImportError:
    logger.error("OpenAI package required for HybridOCRService")
    raise


@dataclass
class OCRResult:
    """Standard OCR result format for hybrid pipeline."""
    success: bool
    extracted_text: str
    latex: str
    confidence: float
    problem_type: str = "unknown"
    math_detected: bool = False
    method_used: str = "unknown"
    uncertain_regions: list = field(default_factory=list)
    verification_result: Optional[Dict] = None
    error: Optional[str] = None


# Verification prompt for GPT-4o stage
VERIFICATION_PROMPT = """A specialized math OCR system extracted the following from this image:

EXTRACTED TEXT: {extracted_text}
LATEX: {latex}
CONFIDENCE: {confidence}

Looking at the attached image, verify this extraction:
1. Is the extraction accurate? (yes/no)
2. If no, what corrections are needed?
3. Provide the corrected result if different.

Respond ONLY with this JSON format:
{{
    "accurate": true/false,
    "corrections": "description of corrections or null",
    "corrected_text": "corrected plain text or null",
    "corrected_latex": "corrected LaTeX or null",
    "confidence": 0.95
}}"""

# Image optimization constants
MAX_IMAGE_WIDTH = 1600  # Max width for OCR processing
MAX_IMAGE_HEIGHT = 1200  # Max height for OCR processing
JPEG_QUALITY = 85  # JPEG compression quality


def optimize_image_for_ocr(image_path: str) -> tuple[str, dict]:
    """Optimize image for OCR processing by resizing large images.

    Args:
        image_path: Path to the original image

    Returns:
        Tuple of (optimized_image_path, optimization_info)
        If no optimization needed, returns original path
    """
    optimization_info = {
        'optimized': False,
        'original_size': None,
        'new_size': None,
        'reduction_percent': 0
    }

    try:
        with Image.open(image_path) as img:
            original_width, original_height = img.size
            optimization_info['original_size'] = (original_width, original_height)

            # Check if resizing is needed
            if original_width <= MAX_IMAGE_WIDTH and original_height <= MAX_IMAGE_HEIGHT:
                logger.info(f"Image {original_width}x{original_height} within limits, no optimization needed")
                return image_path, optimization_info

            # Calculate new dimensions maintaining aspect ratio
            ratio = min(MAX_IMAGE_WIDTH / original_width, MAX_IMAGE_HEIGHT / original_height)
            new_width = int(original_width * ratio)
            new_height = int(original_height * ratio)

            logger.info(f"Resizing image from {original_width}x{original_height} to {new_width}x{new_height}")

            # Resize with high quality
            resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

            # Convert RGBA to RGB if needed (for JPEG)
            if resized_img.mode == 'RGBA':
                background = Image.new('RGB', resized_img.size, (255, 255, 255))
                background.paste(resized_img, mask=resized_img.split()[3])
                resized_img = background

            # Save to temp file
            temp_dir = os.path.dirname(image_path)
            base_name = os.path.basename(image_path)
            name_without_ext = os.path.splitext(base_name)[0]
            optimized_path = os.path.join(temp_dir, f"{name_without_ext}_optimized.jpg")

            resized_img.save(optimized_path, 'JPEG', quality=JPEG_QUALITY, optimize=True)

            # Calculate reduction
            original_file_size = os.path.getsize(image_path)
            new_file_size = os.path.getsize(optimized_path)
            reduction = ((original_file_size - new_file_size) / original_file_size) * 100

            optimization_info['optimized'] = True
            optimization_info['new_size'] = (new_width, new_height)
            optimization_info['reduction_percent'] = round(reduction, 1)
            optimization_info['original_file_size'] = original_file_size
            optimization_info['new_file_size'] = new_file_size

            logger.info(f"Image optimized: {reduction:.1f}% size reduction")

            return optimized_path, optimization_info

    except Exception as e:
        logger.error(f"Image optimization failed: {e}")
        return image_path, optimization_info


# Progress stages for WebSocket updates
class OCRProgressStage:
    STARTED = "started"
    OPTIMIZING = "optimizing_image"
    PIX2TEXT_LOADING = "loading_pix2text_models"
    PIX2TEXT_PROCESSING = "pix2text_processing"
    GPT4O_VERIFYING = "gpt4o_verifying"
    GPT4O_PROCESSING = "gpt4o_processing"
    COMPLETED = "completed"
    ERROR = "error"


class HybridOCRService:
    """Two-stage OCR service using Pix2Text + GPT-4o verification.

    Stage 1: Pix2Text extracts text with LaTeX formatting (specialized math OCR)
    Stage 2: GPT-4o verifies and corrects if confidence < threshold

    Fallback: Uses GPT-4o only if Pix2Text is unavailable.
    """

    def __init__(
        self,
        verification_threshold: float = 0.9,
        model_name: str = "gpt-4o"
    ):
        """Initialize Hybrid OCR Service.

        Args:
            verification_threshold: Confidence threshold for skipping GPT-4o verification
            model_name: OpenAI model name for verification stage
        """
        self.verification_threshold = verification_threshold
        self.model_name = model_name
        self.pix2text_available = PIX2TEXT_AVAILABLE

        # Initialize Pix2Text if available
        self.p2t = None
        if self.pix2text_available:
            try:
                self.p2t = Pix2Text()
                logger.info("Pix2Text initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Pix2Text: {e}")
                self.pix2text_available = False

        # Initialize OpenAI client
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            logger.error("OPENAI_API_KEY not found")
            raise ValueError("OPENAI_API_KEY is required")

        self.openai_client = OpenAI(api_key=api_key)
        logger.info(f"HybridOCRService initialized. Pix2Text: {self.pix2text_available}")

    def extract(
        self,
        image_path: str,
        subject: str = None,
        method: Literal["hybrid", "gpt4o", "pix2text"] = "hybrid",
        progress_callback: Optional[Callable[[str, str, Optional[int]], None]] = None
    ) -> Dict[str, Any]:
        """Extract text from image using specified method.

        Args:
            image_path: Path to image file
            subject: Optional subject hint ('algebra', 'geometry', 'arithmetic')
            method: OCR method to use ('hybrid', 'gpt4o', 'pix2text')
            progress_callback: Optional callback for progress updates
                               Signature: (stage: str, message: str, percent: Optional[int])

        Returns:
            OCRResult dictionary with extracted text, latex, confidence, and method used
        """
        logger.info(f"HybridOCR extract: {image_path}, method={method}, subject={subject}")

        def emit_progress(stage: str, message: str, percent: Optional[int] = None):
            """Helper to emit progress updates."""
            if progress_callback:
                try:
                    progress_callback(stage, message, percent)
                except Exception as e:
                    logger.warning(f"Progress callback failed: {e}")

        try:
            emit_progress(OCRProgressStage.STARTED, "Starting OCR processing", 0)

            # Step 1: Optimize image
            emit_progress(OCRProgressStage.OPTIMIZING, "Optimizing image for processing", 10)
            optimized_path, optimization_info = optimize_image_for_ocr(image_path)

            if optimization_info.get('optimized'):
                logger.info(f"Using optimized image: {optimization_info}")

            # Route to appropriate method
            if method == "gpt4o":
                emit_progress(OCRProgressStage.GPT4O_PROCESSING, "Processing with GPT-4o Vision", 30)
                result = self._extract_gpt4o_only(optimized_path, subject)
            elif method == "pix2text":
                if not self.pix2text_available:
                    emit_progress(OCRProgressStage.ERROR, "Pix2Text not available", None)
                    return self._error_result(
                        "Pix2Text not available. Use method='hybrid' or 'gpt4o'",
                        method="pix2text"
                    )
                emit_progress(OCRProgressStage.PIX2TEXT_PROCESSING, "Processing with Pix2Text", 30)
                result = self._extract_pix2text_only(optimized_path)
            else:
                # Hybrid method (default)
                result = self._extract_hybrid(optimized_path, subject, emit_progress)

            # Add optimization info to result
            result['image_optimization'] = optimization_info

            emit_progress(OCRProgressStage.COMPLETED, "OCR processing complete", 100)
            return result

        except Exception as e:
            logger.error(f"HybridOCR error: {e}")
            emit_progress(OCRProgressStage.ERROR, f"OCR error: {str(e)}", None)
            return self._error_result(str(e), method=method)

    def _extract_hybrid(
        self,
        image_path: str,
        subject: str = None,
        emit_progress: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """Two-stage hybrid extraction: Pix2Text -> GPT-4o verification.

        Args:
            image_path: Path to image file
            subject: Optional subject hint
            emit_progress: Optional progress callback

        Returns:
            Combined result with verification
        """
        def progress(stage: str, message: str, percent: Optional[int] = None):
            if emit_progress:
                emit_progress(stage, message, percent)

        # Stage 1: Try Pix2Text first
        if self.pix2text_available:
            progress(OCRProgressStage.PIX2TEXT_PROCESSING, "Running Pix2Text math OCR", 30)
            p2t_result = self._extract_pix2text_only(image_path)

            if p2t_result.get('success'):
                confidence = p2t_result.get('confidence', 0)

                # High confidence: skip verification
                if confidence >= self.verification_threshold:
                    logger.info(f"Pix2Text confidence {confidence:.2f} >= {self.verification_threshold}, skipping verification")
                    p2t_result['method_used'] = 'pix2text'
                    progress(OCRProgressStage.COMPLETED, "High confidence result - no verification needed", 90)
                    return p2t_result

                # Low confidence: verify with GPT-4o
                logger.info(f"Pix2Text confidence {confidence:.2f} < {self.verification_threshold}, verifying with GPT-4o")
                progress(OCRProgressStage.GPT4O_VERIFYING, "Verifying with GPT-4o Vision", 60)
                return self._verify_with_gpt4o(image_path, p2t_result)

        # Fallback: GPT-4o only
        logger.info("Falling back to GPT-4o only mode")
        progress(OCRProgressStage.GPT4O_PROCESSING, "Processing with GPT-4o Vision (fallback)", 30)
        return self._extract_gpt4o_only(image_path, subject)

    def _extract_pix2text_only(self, image_path: str) -> Dict[str, Any]:
        """Extract using Pix2Text only.

        Args:
            image_path: Path to image file

        Returns:
            OCRResult dictionary
        """
        if not self.pix2text_available or not self.p2t:
            return self._error_result("Pix2Text not available", method="pix2text")

        try:
            # Pix2Text extraction
            result = self.p2t.recognize(image_path)

            # Handle different result formats
            if isinstance(result, str):
                extracted_text = result
                latex = result if '$' in result or '\\' in result else f"${result}$"
                confidence = 0.85  # Default confidence for string results
            elif isinstance(result, dict):
                extracted_text = result.get('text', str(result))
                latex = result.get('latex', extracted_text)
                confidence = result.get('confidence', result.get('score', 0.85))
            else:
                extracted_text = str(result)
                latex = f"${extracted_text}$"
                confidence = 0.8

            return {
                'success': True,
                'extracted_text': extracted_text,
                'latex': latex,
                'confidence': float(confidence),
                'problem_type': self._detect_problem_type(extracted_text),
                'math_detected': True,
                'method_used': 'pix2text',
                'uncertain_regions': []
            }

        except Exception as e:
            logger.error(f"Pix2Text extraction failed: {e}")
            return self._error_result(f"Pix2Text extraction failed: {e}", method="pix2text")

    def _extract_gpt4o_only(self, image_path: str, subject: str = None) -> Dict[str, Any]:
        """Extract using GPT-4o Vision only (fallback mode).

        Args:
            image_path: Path to image file
            subject: Optional subject hint

        Returns:
            OCRResult dictionary
        """
        try:
            # Import the enhanced VisionService from Story 8-1
            from app.services.vision_service import VisionService

            vision_service = VisionService(model_name=self.model_name)
            result = vision_service.extract_text_from_image(image_path, subject=subject)

            # Add method_used field
            result['method_used'] = 'gpt4o'
            return result

        except Exception as e:
            logger.error(f"GPT-4o extraction failed: {e}")
            return self._error_result(f"GPT-4o extraction failed: {e}", method="gpt4o")

    def _verify_with_gpt4o(self, image_path: str, p2t_result: Dict) -> Dict[str, Any]:
        """Verify Pix2Text result with GPT-4o.

        Args:
            image_path: Path to original image
            p2t_result: Pix2Text extraction result

        Returns:
            Verified/corrected result
        """
        try:
            # Encode image
            with open(image_path, "rb") as f:
                image_data = f.read()
                base64_image = base64.b64encode(image_data).decode('utf-8')

            # Determine image format
            image_format = image_path.split('.')[-1].lower()
            if image_format == 'jpg':
                image_format = 'jpeg'

            # Build verification prompt
            prompt = VERIFICATION_PROMPT.format(
                extracted_text=p2t_result.get('extracted_text', ''),
                latex=p2t_result.get('latex', ''),
                confidence=p2t_result.get('confidence', 0)
            )

            # Call GPT-4o for verification
            response = self.openai_client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
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
                max_tokens=500,
                temperature=0.0
            )

            raw_response = response.choices[0].message.content.strip()
            logger.info(f"GPT-4o verification response: {raw_response}")

            # Parse verification result
            verification = self._parse_verification_response(raw_response)

            # Build final result
            if verification.get('accurate', False):
                # Original Pix2Text result was accurate
                result = p2t_result.copy()
                result['method_used'] = 'hybrid_verified'
                result['verification_result'] = verification
                result['confidence'] = max(p2t_result.get('confidence', 0), verification.get('confidence', 0.9))
            else:
                # Use corrected result from GPT-4o
                result = {
                    'success': True,
                    'extracted_text': verification.get('corrected_text') or p2t_result.get('extracted_text', ''),
                    'latex': verification.get('corrected_latex') or p2t_result.get('latex', ''),
                    'confidence': verification.get('confidence', 0.85),
                    'problem_type': self._detect_problem_type(verification.get('corrected_text', '')),
                    'math_detected': True,
                    'method_used': 'hybrid_corrected',
                    'uncertain_regions': [],
                    'verification_result': verification,
                    'original_pix2text': p2t_result
                }

            return result

        except Exception as e:
            logger.error(f"GPT-4o verification failed: {e}")
            # Fall back to Pix2Text result if verification fails
            p2t_result['method_used'] = 'pix2text_unverified'
            p2t_result['verification_error'] = str(e)
            return p2t_result

    def _parse_verification_response(self, raw_response: str) -> Dict[str, Any]:
        """Parse GPT-4o verification response JSON.

        Args:
            raw_response: Raw response from GPT-4o

        Returns:
            Parsed verification dictionary
        """
        try:
            json_match = re.search(r'\{[\s\S]*\}', raw_response)
            if json_match:
                return json.loads(json_match.group())
        except (json.JSONDecodeError, AttributeError) as e:
            logger.warning(f"Failed to parse verification response: {e}")

        # Default to accurate if parsing fails
        return {
            'accurate': True,
            'corrections': None,
            'corrected_text': None,
            'corrected_latex': None,
            'confidence': 0.8
        }

    def _detect_problem_type(self, text: str) -> str:
        """Detect problem type from extracted text.

        Args:
            text: Extracted text

        Returns:
            Problem type: 'algebra', 'geometry', or 'arithmetic'
        """
        if not text:
            return 'unknown'

        text_lower = text.lower()

        # Check for geometry indicators
        geometry_terms = ['triangle', 'circle', 'rectangle', 'square', 'angle',
                         'parallel', 'perpendicular', 'radius', 'diameter']
        if any(term in text_lower for term in geometry_terms):
            return 'geometry'

        # Check for algebra indicators (variables)
        if re.search(r'[a-zA-Z]\s*[+\-*/=]', text) or re.search(r'[+\-*/=]\s*[a-zA-Z]', text):
            return 'algebra'

        # Default to arithmetic
        if re.search(r'\d+\s*[+\-*/=]\s*\d+', text):
            return 'arithmetic'

        return 'unknown'

    def _error_result(self, error_message: str, method: str = "unknown") -> Dict[str, Any]:
        """Create error result dictionary.

        Args:
            error_message: Error description
            method: Method that failed

        Returns:
            Error result dictionary
        """
        return {
            'success': False,
            'error': error_message,
            'extracted_text': '',
            'latex': '',
            'confidence': 0.0,
            'problem_type': 'unknown',
            'math_detected': False,
            'method_used': method,
            'uncertain_regions': []
        }

    def check_availability(self) -> Dict[str, Any]:
        """Check service availability and methods.

        Returns:
            Availability status for each method
        """
        return {
            'hybrid_available': self.pix2text_available,
            'pix2text_available': self.pix2text_available,
            'gpt4o_available': True,  # Always available with OpenAI key
            'verification_threshold': self.verification_threshold,
            'recommended_method': 'hybrid' if self.pix2text_available else 'gpt4o'
        }
