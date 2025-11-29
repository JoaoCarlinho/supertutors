"""Unit tests for Vision Service OCR functionality (Story 8-1).

Tests for:
- AC-1: Temperature set to 0.0 for deterministic OCR
- AC-2: Chain-of-thought prompt with 5 steps (SCAN, SEGMENT, TRANSCRIBE, VERIFY, OUTPUT)
- AC-3: Uncertainty markers protocol ([unclear:x/y], [unreadable])
- AC-4: Response schema includes latex, uncertain_regions, problem_type
- AC-5: GEOMETRY_PROMPT with JSON structure
- AC-6: Accuracy benchmarking
"""
import pytest
import json
import re
from unittest.mock import Mock, patch, MagicMock
from app.services.vision_service import (
    VisionService,
    OCR_PROMPT,
    GEOMETRY_PROMPT,
    UncertainRegion
)


class TestVisionServicePrompts:
    """Test suite for OCR prompts (AC-2, AC-5)."""

    def test_ocr_prompt_has_five_steps(self):
        """AC-2: OCR_PROMPT contains all 5 chain-of-thought steps."""
        steps = ['STEP 1 - SCAN', 'STEP 2 - SEGMENT', 'STEP 3 - TRANSCRIBE',
                 'STEP 4 - VERIFY', 'STEP 5 - OUTPUT']
        for step in steps:
            assert step in OCR_PROMPT, f"Missing step: {step}"

    def test_ocr_prompt_has_uncertainty_protocol(self):
        """AC-3: OCR_PROMPT includes uncertainty protocol."""
        assert '[unclear:' in OCR_PROMPT
        assert '[unreadable]' in OCR_PROMPT
        assert 'UNCERTAINTY PROTOCOL' in OCR_PROMPT

    def test_ocr_prompt_requests_json_output(self):
        """AC-4: OCR_PROMPT requests JSON format output."""
        assert '"extracted_text"' in OCR_PROMPT
        assert '"latex"' in OCR_PROMPT
        assert '"confidence"' in OCR_PROMPT
        assert '"problem_type"' in OCR_PROMPT
        assert '"uncertain_regions"' in OCR_PROMPT

    def test_geometry_prompt_has_five_steps(self):
        """AC-5: GEOMETRY_PROMPT contains all 5 steps."""
        steps = ['STEP 1 - IDENTIFY SHAPES', 'STEP 2 - EXTRACT MEASUREMENTS',
                 'STEP 3 - IDENTIFY LABELS', 'STEP 4 - EXTRACT RELATIONSHIPS',
                 'STEP 5 - OUTPUT']
        for step in steps:
            assert step in GEOMETRY_PROMPT, f"Missing step: {step}"

    def test_geometry_prompt_requests_shape_json(self):
        """AC-5: GEOMETRY_PROMPT requests shapes JSON format."""
        assert '"shapes"' in GEOMETRY_PROMPT
        assert '"relationships"' in GEOMETRY_PROMPT
        assert '"problem_text"' in GEOMETRY_PROMPT
        assert '"given_information"' in GEOMETRY_PROMPT
        assert '"confidence"' in GEOMETRY_PROMPT

    def test_geometry_prompt_supports_shape_types(self):
        """AC-5: GEOMETRY_PROMPT supports required shape types."""
        shape_types = ['triangle', 'circle', 'rectangle', 'polygon', 'line', 'angle']
        for shape in shape_types:
            assert shape in GEOMETRY_PROMPT, f"Missing shape type: {shape}"

    def test_geometry_prompt_supports_relationships(self):
        """AC-5: GEOMETRY_PROMPT supports required relationship types."""
        relationships = ['parallel', 'perpendicular', 'congruent', 'similar']
        for rel in relationships:
            assert rel in GEOMETRY_PROMPT, f"Missing relationship type: {rel}"


class TestVisionServiceTemperature:
    """Test suite for temperature setting (AC-1)."""

    @patch('app.services.vision_service.OpenAI')
    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'})
    def test_temperature_is_zero(self, mock_openai):
        """AC-1: Temperature is set to 0.0 for deterministic OCR."""
        # Setup mock
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"extracted_text": "x+1=2", "latex": "$x+1=2$", "confidence": 0.95, "problem_type": "algebra", "uncertain_regions": []}'
        mock_client.chat.completions.create.return_value = mock_response

        # Create service and call
        service = VisionService()

        # Create a mock image file with proper context manager
        mock_file = MagicMock()
        mock_file.read.return_value = b'fake image data'
        mock_file.__enter__ = MagicMock(return_value=mock_file)
        mock_file.__exit__ = MagicMock(return_value=False)

        with patch('builtins.open', return_value=mock_file):
            service.extract_text_from_image('/fake/path.png')

        # Verify temperature was set to 0.0
        call_args = mock_client.chat.completions.create.call_args
        assert call_args is not None, "API was not called"
        assert call_args.kwargs.get('temperature') == 0.0, \
            f"Temperature should be 0.0, got {call_args.kwargs.get('temperature')}"


class TestVisionServiceUncertaintyParsing:
    """Test suite for uncertainty marker parsing (AC-3)."""

    @patch('app.services.vision_service.OpenAI')
    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'})
    def setup_method(self, method, mock_openai):
        """Set up test fixtures."""
        mock_openai.return_value = MagicMock()
        self.service = VisionService()

    def test_extract_unclear_markers(self):
        """AC-3: Extract [unclear:x/y] markers correctly."""
        text = "The equation is [unclear:2/z]x + [unclear:3/8] = 5"
        regions = self.service._extract_uncertainty_markers(text)

        assert len(regions) == 2
        assert regions[0]['character'] == '2'
        assert regions[0]['alternatives'] == ['2', 'z']
        assert regions[1]['character'] == '3'
        assert regions[1]['alternatives'] == ['3', '8']

    def test_extract_unreadable_markers(self):
        """AC-3: Extract [unreadable] markers correctly."""
        text = "The equation is x + [unreadable] = 5"
        regions = self.service._extract_uncertainty_markers(text)

        assert len(regions) == 1
        assert regions[0]['character'] == '?'
        assert regions[0]['confidence'] == 0.0
        assert regions[0]['alternatives'] == []

    def test_clean_unclear_markers(self):
        """AC-3: Clean [unclear:x/y] markers to best guess."""
        text = "x + [unclear:2/z] = [unclear:5/s]"
        cleaned = self.service._clean_uncertainty_markers(text)

        assert cleaned == "x + 2 = 5"
        assert '[unclear' not in cleaned

    def test_clean_unreadable_markers(self):
        """AC-3: Clean [unreadable] markers to placeholder."""
        text = "x + [unreadable] = 5"
        cleaned = self.service._clean_uncertainty_markers(text)

        assert cleaned == "x + ? = 5"
        assert '[unreadable]' not in cleaned


class TestVisionServiceResponseParsing:
    """Test suite for response parsing (AC-4)."""

    @patch('app.services.vision_service.OpenAI')
    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'})
    def setup_method(self, method, mock_openai):
        """Set up test fixtures."""
        mock_openai.return_value = MagicMock()
        self.service = VisionService()

    def test_parse_valid_json_response(self):
        """AC-4: Parse valid JSON OCR response correctly."""
        json_response = '''{
            "extracted_text": "3x + 2 = 5",
            "latex": "$3x + 2 = 5$",
            "confidence": 0.92,
            "problem_type": "algebra",
            "uncertain_regions": [
                {"position": 0, "character": "3", "confidence": 0.8, "alternatives": ["3", "8"]}
            ]
        }'''

        result = self.service._parse_ocr_response(json_response)

        assert result['success'] is True
        assert result['extracted_text'] == "3x + 2 = 5"
        assert result['latex'] == "$3x + 2 = 5$"
        assert result['confidence'] == 0.92
        assert result['problem_type'] == "algebra"
        assert len(result['uncertain_regions']) == 1

    def test_parse_geometry_json_response(self):
        """AC-4: Parse geometry JSON response with shapes."""
        json_response = '''{
            "shapes": [
                {"type": "triangle", "labels": ["A", "B", "C"]}
            ],
            "relationships": [
                {"type": "perpendicular", "elements": ["AB", "BC"]}
            ],
            "problem_text": ["Find the area"],
            "given_information": ["AB = 3", "BC = 4"],
            "confidence": 0.85
        }'''

        result = self.service._parse_ocr_response(json_response, subject='geometry')

        assert result['success'] is True
        assert len(result['shapes']) == 1
        assert result['shapes'][0]['type'] == 'triangle'
        assert len(result['relationships']) == 1
        assert result['confidence'] == 0.85

    def test_parse_plain_text_fallback(self):
        """AC-4: Parse plain text response when JSON fails."""
        plain_response = "Linear equation: $3x + 2 = 5$"

        result = self.service._parse_plain_text_response(plain_response)

        assert result['success'] is True
        assert '$3x + 2 = 5$' in result['latex']

    def test_response_includes_all_required_fields(self):
        """AC-4: Response includes latex, uncertain_regions, problem_type."""
        json_response = '''{
            "extracted_text": "x = 5",
            "latex": "$x = 5$",
            "confidence": 0.95,
            "problem_type": "algebra",
            "uncertain_regions": []
        }'''

        result = self.service._parse_ocr_response(json_response)

        assert 'latex' in result
        assert 'uncertain_regions' in result
        assert 'problem_type' in result
        assert 'confidence' in result
        assert 'extracted_text' in result


class TestVisionServiceProblemTypeDetection:
    """Test suite for problem type detection (AC-4)."""

    @patch('app.services.vision_service.OpenAI')
    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'})
    def setup_method(self, method, mock_openai):
        """Set up test fixtures."""
        mock_openai.return_value = MagicMock()
        self.service = VisionService()

    def test_detect_algebra_with_variables(self):
        """AC-4: Detect algebra when text has variables."""
        assert self.service._detect_problem_type("x + 5 = 10") == "algebra"
        assert self.service._detect_problem_type("2y - 3 = 7") == "algebra"
        assert self.service._detect_problem_type("z = 4") == "algebra"

    def test_detect_geometry_with_shapes(self):
        """AC-4: Detect geometry when text mentions shapes."""
        assert self.service._detect_problem_type("triangle ABC") == "geometry"
        assert self.service._detect_problem_type("circle with radius 5") == "geometry"
        assert self.service._detect_problem_type("angle ABC = 90°") == "geometry"
        assert self.service._detect_problem_type("parallel lines") == "geometry"

    def test_detect_arithmetic_with_numbers(self):
        """AC-4: Detect arithmetic when text has only numbers."""
        assert self.service._detect_problem_type("5 + 3 = 8") == "arithmetic"
        assert self.service._detect_problem_type("12 * 4") == "arithmetic"
        assert self.service._detect_problem_type("100 / 25") == "arithmetic"


class TestVisionServiceConfidenceCalculation:
    """Test suite for confidence calculation (AC-4)."""

    @patch('app.services.vision_service.OpenAI')
    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'})
    def setup_method(self, method, mock_openai):
        """Set up test fixtures."""
        mock_openai.return_value = MagicMock()
        self.service = VisionService()

    def test_high_confidence_no_markers(self):
        """AC-4: High confidence when no uncertainty markers."""
        regions = []
        confidence = self.service._calculate_confidence_from_markers(regions, "3x + 2 = 5")
        assert confidence >= 0.9

    def test_reduced_confidence_with_unclear_markers(self):
        """AC-4: Confidence reduced for unclear markers."""
        regions = [
            {'position': 0, 'character': '3', 'confidence': 0.6, 'alternatives': ['3', '8']}
        ]
        confidence = self.service._calculate_confidence_from_markers(regions, "3x + 2 = 5")
        assert confidence < 0.92  # Lower than base

    def test_low_confidence_with_unreadable_markers(self):
        """AC-4: Confidence significantly reduced for unreadable markers."""
        regions = [
            {'position': 0, 'character': '?', 'confidence': 0.0, 'alternatives': []}
        ]
        confidence = self.service._calculate_confidence_from_markers(regions, "?x + 2 = 5")
        assert confidence < 0.85

    def test_multiple_markers_compound_penalty(self):
        """AC-4: Multiple markers compound confidence penalty."""
        regions = [
            {'position': 0, 'character': '3', 'confidence': 0.6, 'alternatives': ['3', '8']},
            {'position': 5, 'character': '2', 'confidence': 0.6, 'alternatives': ['2', 'z']},
            {'position': 10, 'character': '5', 'confidence': 0.6, 'alternatives': ['5', 's']}
        ]
        confidence = self.service._calculate_confidence_from_markers(regions, "3x + 2 = 5")
        assert confidence < 0.8  # Significantly lower with 3 markers


class TestVisionServiceMathDetection:
    """Test suite for math content detection."""

    @patch('app.services.vision_service.OpenAI')
    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'})
    def setup_method(self, method, mock_openai):
        """Set up test fixtures."""
        mock_openai.return_value = MagicMock()
        self.service = VisionService()

    def test_detect_latex_delimiters(self):
        """Detect math with LaTeX delimiters."""
        assert self.service._detect_math("$x + 5$") is True
        assert self.service._detect_math("\\frac{1}{2}") is True
        assert self.service._detect_math("\\sqrt{16}") is True

    def test_detect_math_symbols(self):
        """Detect math with mathematical symbols."""
        assert self.service._detect_math("x = 5") is True
        assert self.service._detect_math("a ≤ b") is True
        assert self.service._detect_math("π r²") is True

    def test_detect_equations(self):
        """Detect equations with variables and operators."""
        assert self.service._detect_math("x + 5") is True
        assert self.service._detect_math("2y - 3") is True

    def test_detect_arithmetic(self):
        """Detect arithmetic expressions."""
        assert self.service._detect_math("5 + 3") is True
        assert self.service._detect_math("12 * 4") is True

    def test_no_math_plain_text(self):
        """No math detection for plain text."""
        assert self.service._detect_math("Hello world") is False
        assert self.service._detect_math("This is a sentence") is False

    def test_no_math_empty_string(self):
        """No math detection for empty string."""
        assert self.service._detect_math("") is False
        assert self.service._detect_math(None) is False


class TestVisionServiceGeometryRouting:
    """Test suite for geometry-specific routing (AC-5)."""

    @patch('app.services.vision_service.OpenAI')
    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'})
    def test_geometry_subject_uses_geometry_prompt(self, mock_openai):
        """AC-5: subject='geometry' routes to GEOMETRY_PROMPT."""
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"shapes": [], "relationships": [], "problem_text": [], "given_information": [], "confidence": 0.9}'
        mock_client.chat.completions.create.return_value = mock_response

        service = VisionService()

        # Create a mock image file with proper context manager
        mock_file = MagicMock()
        mock_file.read.return_value = b'fake image data'
        mock_file.__enter__ = MagicMock(return_value=mock_file)
        mock_file.__exit__ = MagicMock(return_value=False)

        with patch('builtins.open', return_value=mock_file):
            service.extract_text_from_image('/fake/path.png', subject='geometry')

        # Verify GEOMETRY_PROMPT was used
        call_args = mock_client.chat.completions.create.call_args
        assert call_args is not None, "API was not called"
        prompt_used = call_args.kwargs['messages'][0]['content'][0]['text']
        assert 'IDENTIFY SHAPES' in prompt_used

    @patch('app.services.vision_service.OpenAI')
    @patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'})
    def test_algebra_subject_uses_ocr_prompt(self, mock_openai):
        """AC-5: subject='algebra' routes to OCR_PROMPT."""
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"extracted_text": "x=5", "latex": "$x=5$", "confidence": 0.95, "problem_type": "algebra", "uncertain_regions": []}'
        mock_client.chat.completions.create.return_value = mock_response

        service = VisionService()

        # Create a mock image file with proper context manager
        mock_file = MagicMock()
        mock_file.read.return_value = b'fake image data'
        mock_file.__enter__ = MagicMock(return_value=mock_file)
        mock_file.__exit__ = MagicMock(return_value=False)

        with patch('builtins.open', return_value=mock_file):
            service.extract_text_from_image('/fake/path.png', subject='algebra')

        # Verify OCR_PROMPT was used (with algebra hint)
        call_args = mock_client.chat.completions.create.call_args
        assert call_args is not None, "API was not called"
        prompt_used = call_args.kwargs['messages'][0]['content'][0]['text']
        assert 'ALGEBRA' in prompt_used
        assert 'STEP 1 - SCAN' in prompt_used


class TestUncertainRegionDataclass:
    """Test suite for UncertainRegion dataclass."""

    def test_uncertain_region_creation(self):
        """Test UncertainRegion dataclass fields."""
        region = UncertainRegion(
            position=5,
            character='2',
            confidence=0.6,
            alternatives=['2', 'z']
        )
        assert region.position == 5
        assert region.character == '2'
        assert region.confidence == 0.6
        assert region.alternatives == ['2', 'z']

    def test_uncertain_region_default_alternatives(self):
        """Test UncertainRegion with default alternatives."""
        region = UncertainRegion(
            position=0,
            character='x',
            confidence=0.9
        )
        assert region.alternatives == []
