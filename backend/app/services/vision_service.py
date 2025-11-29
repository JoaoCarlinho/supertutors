"""Vision AI Service - OCR extraction using OpenAI GPT-4 Vision.

Enhanced with chain-of-thought prompting for improved OCR accuracy (Story 8-1).
Temperature set to 0.0 for deterministic output per research findings.
Includes uncertainty markers and structured JSON output.
"""
import logging
import os
import re
import base64
import time
import random
import hashlib
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict, field
from openai import OpenAI

logger = logging.getLogger(__name__)


@dataclass
class UncertainRegion:
    """Represents an uncertain character region in OCR output (AC-4)."""
    position: int
    character: str
    confidence: float
    alternatives: List[str] = field(default_factory=list)


# Chain-of-thought OCR prompt with 5-step structure (AC-2)
# Includes uncertainty protocol (AC-3) and structured output format (AC-4)
OCR_PROMPT = """You are performing OCR (Optical Character Recognition) on an image containing handwritten math.
Your task is to EXTRACT EXACTLY what is written - never invent or guess.

STEP 1 - SCAN:
Look at the entire image. Describe all regions that contain writing.
Note the layout: is it a single equation, multiple lines, or mixed content?

STEP 2 - SEGMENT:
Identify each distinct symbol/character from left to right, top to bottom.
List them in order: "I see: [first char], [second char], [third char]..."

STEP 3 - TRANSCRIBE:
For each symbol, state what you see:
- Clear characters: write them directly
- Unclear characters: mark as [unclear:best_guess/alternative] (e.g., [unclear:2/z])
- Illegible content: mark as [unreadable]
- Never invent symbols that aren't visible in the image

STEP 4 - VERIFY:
Re-read your transcription against the image.
Check each character matches what's actually written.
Note any corrections needed.

STEP 5 - OUTPUT:
Provide the final result in this JSON format:
{
    "extracted_text": "the plain text transcription",
    "latex": "$LaTeX formatted equation$",
    "problem_type": "algebra|geometry|arithmetic",
    "uncertain_regions": [
        {"position": 0, "character": "x", "confidence": 0.75, "alternatives": ["x", "z"]}
    ],
    "confidence": 0.92
}

UNCERTAINTY PROTOCOL:
- If a character is unclear: [unclear:best_guess/alternative]
- If completely illegible: [unreadable]
- Never invent symbols not visible in the image
- Confidence should reflect your certainty (0.0-1.0)

PROBLEM TYPE DETECTION:
- ALGEBRA: contains variables (x, y, z, etc.) with equations or expressions
- GEOMETRY: contains shapes, angles, measurements, or geometric figures
- ARITHMETIC: only numbers and basic operations (+, -, ×, ÷, =)

Respond ONLY with the JSON object, no additional text."""


# Geometry-specific prompt for structured shape extraction (AC-5)
GEOMETRY_PROMPT = """You are analyzing a geometric diagram or shape image.
Extract all shapes, measurements, labels, and relationships visible in the image.

STEP 1 - IDENTIFY SHAPES:
List all geometric shapes you can see (triangles, circles, rectangles, polygons, lines, angles).

STEP 2 - EXTRACT MEASUREMENTS:
For each shape, note any visible measurements:
- Side lengths (e.g., "3cm", "5 units")
- Angles (e.g., "90°", "45 degrees")
- Radii, diameters for circles
- Any labeled values

STEP 3 - IDENTIFY LABELS:
Note all text labels on the diagram:
- Point labels (A, B, C, etc.)
- Variable labels (x, y, etc.)
- Measurement labels

STEP 4 - EXTRACT RELATIONSHIPS:
Identify geometric relationships:
- Parallel lines (e.g., "AB || CD")
- Perpendicular lines (e.g., "AB ⊥ CD")
- Congruent segments or angles
- Similar shapes

STEP 5 - OUTPUT:
Provide the result in this JSON format:
{
    "shapes": [
        {
            "type": "triangle|circle|rectangle|polygon|line|angle",
            "labels": ["A", "B", "C"],
            "sides": [{"label": "AB", "length": "3cm"}, {"label": "BC", "length": "4cm"}],
            "angles": [{"label": "ABC", "measure": "90°"}],
            "radius": null,
            "area": null
        }
    ],
    "relationships": [
        {"type": "parallel|perpendicular|congruent|similar", "elements": ["AB", "CD"]}
    ],
    "problem_text": ["Find x", "Calculate the area"],
    "given_information": ["AB = 3cm", "angle ABC = 90°"],
    "confidence": 0.85
}

If a measurement is unclear, mark it as: "[unclear:best_guess/alternative]"
If something is unreadable, mark it as: "[unreadable]"

Respond ONLY with the JSON object, no additional text."""


class VisionService:
    """Service for Vision AI OCR using OpenAI GPT-4 Vision.

    Enhanced with chain-of-thought prompting and uncertainty markers (Story 8-1).
    """

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
        """Extract text and math from image using Vision AI with chain-of-thought prompting.

        Args:
            image_path: Path to image file
            subject: Optional subject hint ('algebra', 'geometry', 'arithmetic')

        Returns:
            Dictionary with success, extracted_text, latex, confidence, math_detected,
            problem_type, and uncertain_regions (AC-4 enhanced response schema)
        """
        try:
            logger.info(f"Extracting text from image: {image_path}, subject: {subject}")

            # Encode image as base64
            with open(image_path, "rb") as image_file:
                image_data = image_file.read()
                base64_image = base64.b64encode(image_data).decode('utf-8')

            # Calculate image hash for debugging and cache verification
            image_hash = hashlib.md5(image_data).hexdigest()[:8]
            logger.info(f"Image hash: {image_hash}, size: {len(base64_image)} chars")

            # Determine image format from file extension
            image_format = image_path.split('.')[-1].lower()
            if image_format == 'jpg':
                image_format = 'jpeg'

            # Select prompt based on subject (AC-5: geometry-specific routing)
            if subject and subject.lower() == 'geometry':
                prompt_text = GEOMETRY_PROMPT
                logger.info("Using GEOMETRY_PROMPT for geometry subject")
            else:
                prompt_text = OCR_PROMPT
                # Add subject hint as prefix if provided
                if subject:
                    subject_hints = {
                        'algebra': 'SUBJECT HINT: The student indicated this is an ALGEBRA problem (equations, expressions, variables).\n\n',
                        'arithmetic': 'SUBJECT HINT: The student indicated this is an ARITHMETIC problem (basic calculations).\n\n'
                    }
                    hint = subject_hints.get(subject.lower(), '')
                    if hint:
                        prompt_text = hint + prompt_text

            # Add cache-busting mechanism to force fresh OCR analysis
            cache_buster = f"\n\n[Request ID: {int(time.time() * 1000)}-{random.randint(1000, 9999)}]"
            prompt_text_final = prompt_text + cache_buster

            logger.info(f"OCR request with cache-buster, image hash: {image_hash}")

            # Call OpenAI Vision API with temperature=0.0 for deterministic OCR (AC-1)
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": prompt_text_final
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
                max_tokens=1500,
                temperature=0.0  # Deterministic output for OCR accuracy (AC-1, Story 8-1)
            )

            raw_response = response.choices[0].message.content.strip()
            logger.info(f"RAW OCR OUTPUT: {raw_response}")
            logger.info(f"Subject hint used: {subject}")
            logger.info(f"Image hash: {image_hash} - This verifies unique image processing")

            # Parse structured JSON response (AC-4)
            result = self._parse_ocr_response(raw_response, subject)

            # Detect if math content is present
            result['math_detected'] = self._detect_math(result.get('extracted_text', ''))

            logger.info(
                f"OCR complete. Confidence: {result.get('confidence', 0):.2f}, "
                f"Math detected: {result.get('math_detected')}, "
                f"Problem type: {result.get('problem_type', 'unknown')}"
            )

            return result

        except Exception as e:
            error_msg = f"OpenAI Vision API error: {str(e)}"
            logger.error(f"OCR failed: {error_msg}")
            return {
                'success': False,
                'error': "An error occurred during OCR processing.",
                'extracted_text': '',
                'latex': '',
                'confidence': 0.0,
                'math_detected': False,
                'problem_type': 'unknown',
                'uncertain_regions': []
            }

    def _parse_ocr_response(self, raw_response: str, subject: str = None) -> Dict[str, Any]:
        """Parse OCR response, handling both JSON and plain text formats.

        Args:
            raw_response: Raw response from GPT-4o
            subject: Subject hint used

        Returns:
            Structured response dictionary with all fields (AC-4)
        """
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{[\s\S]*\}', raw_response)
            if json_match:
                json_str = json_match.group()
                parsed = json.loads(json_str)

                # Ensure all required fields exist
                result = {
                    'success': True,
                    'extracted_text': parsed.get('extracted_text', raw_response),
                    'latex': parsed.get('latex', ''),
                    'confidence': float(parsed.get('confidence', 0.85)),
                    'problem_type': parsed.get('problem_type', 'unknown'),
                    'uncertain_regions': parsed.get('uncertain_regions', [])
                }

                # Handle geometry-specific fields
                if subject and subject.lower() == 'geometry':
                    result['shapes'] = parsed.get('shapes', [])
                    result['relationships'] = parsed.get('relationships', [])
                    result['problem_text'] = parsed.get('problem_text', [])
                    result['given_information'] = parsed.get('given_information', [])

                return result

        except (json.JSONDecodeError, AttributeError) as e:
            logger.warning(f"Failed to parse JSON from OCR response: {e}")

        # Fallback: Parse plain text response and extract uncertainty markers
        return self._parse_plain_text_response(raw_response)

    def _parse_plain_text_response(self, raw_response: str) -> Dict[str, Any]:
        """Parse plain text OCR response and extract uncertainty markers (AC-3).

        Args:
            raw_response: Raw text response from GPT-4o

        Returns:
            Structured response dictionary
        """
        # Extract uncertainty markers [unclear:x/y] from text
        uncertain_regions = self._extract_uncertainty_markers(raw_response)

        # Clean text by replacing uncertainty markers with best guess
        cleaned_text = self._clean_uncertainty_markers(raw_response)

        # Try to extract LaTeX if present
        latex = ''
        latex_match = re.search(r'\$([^$]+)\$', raw_response)
        if latex_match:
            latex = f"${latex_match.group(1)}$"

        # Detect problem type from content
        problem_type = self._detect_problem_type(cleaned_text)

        # Calculate confidence based on uncertainty markers
        confidence = self._calculate_confidence_from_markers(uncertain_regions, cleaned_text)

        return {
            'success': True,
            'extracted_text': cleaned_text,
            'latex': latex,
            'confidence': confidence,
            'problem_type': problem_type,
            'uncertain_regions': uncertain_regions
        }

    def _extract_uncertainty_markers(self, text: str) -> List[Dict[str, Any]]:
        """Extract [unclear:x/y] markers from text (AC-3).

        Args:
            text: Text containing uncertainty markers

        Returns:
            List of UncertainRegion dictionaries
        """
        uncertain_regions = []

        # Pattern: [unclear:best_guess/alternative]
        unclear_pattern = r'\[unclear:([^/\]]+)/([^\]]+)\]'
        for match in re.finditer(unclear_pattern, text):
            position = match.start()
            best_guess = match.group(1)
            alternative = match.group(2)

            uncertain_regions.append({
                'position': position,
                'character': best_guess,
                'confidence': 0.6,  # Default confidence for unclear markers
                'alternatives': [best_guess, alternative]
            })

        # Pattern: [unreadable]
        unreadable_pattern = r'\[unreadable\]'
        for match in re.finditer(unreadable_pattern, text):
            uncertain_regions.append({
                'position': match.start(),
                'character': '?',
                'confidence': 0.0,
                'alternatives': []
            })

        return uncertain_regions

    def _clean_uncertainty_markers(self, text: str) -> str:
        """Replace uncertainty markers with best guess values (AC-3).

        Args:
            text: Text containing uncertainty markers

        Returns:
            Cleaned text with markers replaced
        """
        # Replace [unclear:x/y] with just x (best guess)
        cleaned = re.sub(r'\[unclear:([^/\]]+)/[^\]]+\]', r'\1', text)
        # Replace [unreadable] with placeholder
        cleaned = re.sub(r'\[unreadable\]', '?', cleaned)
        return cleaned

    def _detect_problem_type(self, text: str) -> str:
        """Detect problem type from extracted text (AC-4).

        Args:
            text: Extracted text

        Returns:
            Problem type: 'algebra', 'geometry', or 'arithmetic'
        """
        text_lower = text.lower()

        # Check for geometry indicators
        geometry_terms = ['triangle', 'circle', 'rectangle', 'square', 'angle',
                         'parallel', 'perpendicular', 'radius', 'diameter',
                         'area', 'perimeter', 'polygon', 'line segment']
        if any(term in text_lower for term in geometry_terms):
            return 'geometry'

        # Check for algebra indicators (variables)
        if re.search(r'[a-zA-Z]\s*[+\-*/=]', text) or re.search(r'[+\-*/=]\s*[a-zA-Z]', text):
            return 'algebra'

        # Default to arithmetic if only numbers and operators
        if re.search(r'\d+\s*[+\-*/=]\s*\d+', text):
            return 'arithmetic'

        return 'unknown'

    def _calculate_confidence_from_markers(self, uncertain_regions: List[Dict], text: str) -> float:
        """Calculate overall confidence based on uncertainty markers (AC-4).

        Args:
            uncertain_regions: List of uncertain region dictionaries
            text: The extracted text

        Returns:
            Confidence score between 0 and 1
        """
        if not text or len(text) < 3:
            return 0.3

        # Start with high base confidence for GPT-4o
        base_confidence = 0.92

        # Reduce confidence for each uncertain region
        if uncertain_regions:
            # Each uncertainty marker reduces confidence
            penalty_per_marker = 0.05
            total_penalty = min(len(uncertain_regions) * penalty_per_marker, 0.4)
            base_confidence -= total_penalty

        # Check for [unreadable] markers (major confidence hit)
        unreadable_count = sum(1 for region in uncertain_regions if region.get('confidence', 0) == 0)
        if unreadable_count > 0:
            base_confidence -= unreadable_count * 0.1

        return max(0.1, min(base_confidence, 1.0))

    def _estimate_confidence(self, extracted_text: str) -> float:
        """Estimate confidence based on extracted text characteristics.

        DEPRECATED: Use _calculate_confidence_from_markers for new code.

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
        if not text:
            return False

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
