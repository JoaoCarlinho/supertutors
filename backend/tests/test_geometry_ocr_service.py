"""Unit tests for Geometry OCR Service (Story 8-5).

Tests cover:
- GeometryResult data classes (AC-3)
- GeometryOCRService extraction (AC-2, AC-4, AC-5)
- Shape recognition and parsing (AC-4)
- Relationship extraction (AC-5)
- Tutor context formatting (AC-6)
- API endpoint (AC-2)
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import json


class TestGeometryDataClasses:
    """Test geometry data schema classes (AC-3)."""

    def test_side_measurement_creation(self):
        """Test SideMeasurement dataclass."""
        from app.services.geometry_ocr_service import SideMeasurement

        side = SideMeasurement(
            from_point='A',
            to_point='B',
            length='5cm',
            variable=None,
            marked_congruent=False
        )

        assert side.from_point == 'A'
        assert side.to_point == 'B'
        assert side.length == '5cm'
        assert side.variable is None
        assert side.marked_congruent is False

    def test_side_measurement_with_variable(self):
        """Test SideMeasurement with unknown variable."""
        from app.services.geometry_ocr_service import SideMeasurement

        side = SideMeasurement(
            from_point='B',
            to_point='C',
            length=None,
            variable='x',
            marked_congruent=True
        )

        assert side.length is None
        assert side.variable == 'x'
        assert side.marked_congruent is True

    def test_angle_measurement_creation(self):
        """Test AngleMeasurement dataclass."""
        from app.services.geometry_ocr_service import AngleMeasurement

        angle = AngleMeasurement(
            vertex='A',
            measure='90°',
            variable=None,
            marked=True
        )

        assert angle.vertex == 'A'
        assert angle.measure == '90°'
        assert angle.marked is True

    def test_shape_creation(self):
        """Test Shape dataclass with all fields."""
        from app.services.geometry_ocr_service import Shape, SideMeasurement, AngleMeasurement

        shape = Shape(
            type='triangle',
            name='Triangle ABC',
            labels=['A', 'B', 'C'],
            sides=[
                SideMeasurement('A', 'B', '3cm', None, False),
                SideMeasurement('B', 'C', '4cm', None, False),
                SideMeasurement('C', 'A', '5cm', None, False)
            ],
            angles=[
                AngleMeasurement('C', '90°', None, True)
            ],
            properties=['right triangle']
        )

        assert shape.type == 'triangle'
        assert shape.name == 'Triangle ABC'
        assert len(shape.labels) == 3
        assert len(shape.sides) == 3
        assert len(shape.angles) == 1
        assert 'right triangle' in shape.properties

    def test_shape_circle(self):
        """Test Shape dataclass for circle."""
        from app.services.geometry_ocr_service import Shape

        circle = Shape(
            type='circle',
            name='Circle O',
            center='O',
            radius='5cm',
            diameter='10cm'
        )

        assert circle.type == 'circle'
        assert circle.center == 'O'
        assert circle.radius == '5cm'
        assert circle.diameter == '10cm'

    def test_relationship_creation(self):
        """Test Relationship dataclass."""
        from app.services.geometry_ocr_service import Relationship

        rel = Relationship(
            type='parallel',
            elements=['AB', 'CD'],
            marked=True
        )

        assert rel.type == 'parallel'
        assert 'AB' in rel.elements
        assert 'CD' in rel.elements
        assert rel.marked is True

    def test_geometry_result_creation(self):
        """Test GeometryResult dataclass."""
        from app.services.geometry_ocr_service import GeometryResult, Shape, Relationship

        result = GeometryResult(
            success=True,
            shapes=[Shape(type='triangle', labels=['A', 'B', 'C'])],
            relationships=[Relationship(type='perpendicular', elements=['AB', 'BC'])],
            problem_text=['Find the area'],
            given_information=['AB = 3cm', 'BC = 4cm'],
            confidence=0.92
        )

        assert result.success is True
        assert len(result.shapes) == 1
        assert len(result.relationships) == 1
        assert 'Find the area' in result.problem_text
        assert result.confidence == 0.92

    def test_geometry_result_to_dict(self):
        """Test GeometryResult.to_dict() serialization."""
        from app.services.geometry_ocr_service import (
            GeometryResult, Shape, Relationship,
            SideMeasurement, AngleMeasurement
        )

        result = GeometryResult(
            success=True,
            shapes=[
                Shape(
                    type='triangle',
                    name='Triangle ABC',
                    labels=['A', 'B', 'C'],
                    sides=[SideMeasurement('A', 'B', '5cm', None, False)],
                    angles=[AngleMeasurement('C', '90°', None, True)]
                )
            ],
            relationships=[Relationship('parallel', ['AB', 'CD'], True)],
            problem_text=['Find x'],
            given_information=['AB = 5cm'],
            confidence=0.85
        )

        result_dict = result.to_dict()

        assert result_dict['success'] is True
        assert len(result_dict['shapes']) == 1
        assert result_dict['shapes'][0]['type'] == 'triangle'
        assert result_dict['shapes'][0]['sides'][0]['length'] == '5cm'
        assert result_dict['relationships'][0]['type'] == 'parallel'
        assert result_dict['confidence'] == 0.85


class TestGeometryOCRServiceParsing:
    """Test GeometryOCRService JSON parsing (AC-2, AC-4)."""

    @pytest.fixture
    def mock_geometry_service(self):
        """Create GeometryOCRService with mocked OpenAI client."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            with patch('app.services.geometry_ocr_service.OpenAI') as mock_openai:
                from app.services.geometry_ocr_service import GeometryOCRService
                service = GeometryOCRService()
                service.client = mock_openai.return_value
                return service

    def test_parse_geometry_response_triangle(self, mock_geometry_service):
        """Test parsing triangle extraction response."""
        json_response = json.dumps({
            "shapes": [
                {
                    "type": "triangle",
                    "name": "Triangle ABC",
                    "labels": ["A", "B", "C"],
                    "sides": [
                        {"from": "A", "to": "B", "length": "3cm", "variable": None},
                        {"from": "B", "to": "C", "length": "4cm", "variable": None},
                        {"from": "C", "to": "A", "length": "5cm", "variable": None}
                    ],
                    "angles": [
                        {"vertex": "C", "measure": "90°", "variable": None, "marked": True}
                    ],
                    "properties": ["right triangle"]
                }
            ],
            "relationships": [],
            "problem_text": ["Find the area"],
            "given_information": ["Right angle at C"],
            "confidence": 0.95
        })

        result = mock_geometry_service._parse_geometry_response(json_response)

        assert result.success is True
        assert len(result.shapes) == 1
        assert result.shapes[0].type == 'triangle'
        assert result.shapes[0].name == 'Triangle ABC'
        assert len(result.shapes[0].sides) == 3
        assert result.shapes[0].angles[0].measure == '90°'
        assert result.confidence == 0.95

    def test_parse_geometry_response_with_relationships(self, mock_geometry_service):
        """Test parsing response with geometric relationships (AC-5)."""
        json_response = json.dumps({
            "shapes": [
                {"type": "line", "labels": ["A", "B"]},
                {"type": "line", "labels": ["C", "D"]}
            ],
            "relationships": [
                {"type": "parallel", "elements": ["AB", "CD"], "marked": True},
                {"type": "perpendicular", "elements": ["AB", "EF"], "marked": False}
            ],
            "problem_text": [],
            "given_information": ["AB || CD"],
            "confidence": 0.88
        })

        result = mock_geometry_service._parse_geometry_response(json_response)

        assert len(result.relationships) == 2
        assert result.relationships[0].type == 'parallel'
        assert result.relationships[0].marked is True
        assert result.relationships[1].type == 'perpendicular'

    def test_parse_geometry_response_circle(self, mock_geometry_service):
        """Test parsing circle extraction."""
        json_response = json.dumps({
            "shapes": [
                {
                    "type": "circle",
                    "name": "Circle O",
                    "labels": ["O"],
                    "center": "O",
                    "radius": "7cm",
                    "diameter": "14cm",
                    "sides": [],
                    "angles": []
                }
            ],
            "relationships": [],
            "problem_text": ["Find the circumference"],
            "given_information": ["r = 7cm"],
            "confidence": 0.9
        })

        result = mock_geometry_service._parse_geometry_response(json_response)

        assert result.shapes[0].type == 'circle'
        assert result.shapes[0].radius == '7cm'
        assert result.shapes[0].center == 'O'

    def test_parse_geometry_response_invalid_json(self, mock_geometry_service):
        """Test handling of invalid JSON response."""
        invalid_response = "This is not valid JSON"

        result = mock_geometry_service._parse_geometry_response(invalid_response)

        assert result.success is False
        assert 'No structured data' in result.error

    def test_parse_shape_with_variables(self, mock_geometry_service):
        """Test parsing shape with unknown variables."""
        shape_data = {
            "type": "triangle",
            "labels": ["P", "Q", "R"],
            "sides": [
                {"from": "P", "to": "Q", "length": None, "variable": "x"},
                {"from": "Q", "to": "R", "length": "8cm", "variable": None}
            ],
            "angles": [
                {"vertex": "Q", "measure": None, "variable": "θ", "marked": False}
            ]
        }

        shape = mock_geometry_service._parse_shape(shape_data)

        assert shape.sides[0].variable == 'x'
        assert shape.sides[0].length is None
        assert shape.angles[0].variable == 'θ'


class TestGeometryOCRServiceExtraction:
    """Test GeometryOCRService.extract() method (AC-2)."""

    @pytest.fixture
    def mock_geometry_service(self):
        """Create GeometryOCRService with mocked OpenAI client."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            with patch('app.services.geometry_ocr_service.OpenAI') as mock_openai:
                from app.services.geometry_ocr_service import GeometryOCRService
                service = GeometryOCRService()
                service.client = mock_openai.return_value
                return service

    def test_extract_file_not_found(self, mock_geometry_service):
        """Test extraction with non-existent file."""
        result = mock_geometry_service.extract('/nonexistent/path/image.png')

        assert result.success is False
        assert 'not found' in result.error.lower()

    def test_extract_success(self, mock_geometry_service, tmp_path):
        """Test successful geometry extraction."""
        # Create a test image file
        test_image = tmp_path / "triangle.png"
        test_image.write_bytes(b'\x89PNG\r\n\x1a\n' + b'\x00' * 100)

        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps({
            "shapes": [{"type": "triangle", "labels": ["A", "B", "C"]}],
            "relationships": [],
            "problem_text": [],
            "given_information": [],
            "confidence": 0.9
        })
        mock_geometry_service.client.chat.completions.create.return_value = mock_response

        result = mock_geometry_service.extract(str(test_image))

        assert result.success is True
        assert len(result.shapes) == 1
        assert result.shapes[0].type == 'triangle'

    def test_extract_api_error(self, mock_geometry_service, tmp_path):
        """Test handling of API error during extraction."""
        test_image = tmp_path / "test.png"
        test_image.write_bytes(b'\x89PNG\r\n\x1a\n' + b'\x00' * 100)

        mock_geometry_service.client.chat.completions.create.side_effect = Exception("API Error")

        result = mock_geometry_service.extract(str(test_image))

        assert result.success is False
        assert 'failed' in result.error.lower()


class TestGeometryTutorFormatting:
    """Test format_for_tutor() method (AC-6)."""

    @pytest.fixture
    def geometry_service(self):
        """Create GeometryOCRService for testing."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            with patch('app.services.geometry_ocr_service.OpenAI'):
                from app.services.geometry_ocr_service import GeometryOCRService
                return GeometryOCRService()

    def test_format_triangle_for_tutor(self, geometry_service):
        """Test formatting triangle result for tutor context."""
        from app.services.geometry_ocr_service import (
            GeometryResult, Shape, SideMeasurement, AngleMeasurement
        )

        result = GeometryResult(
            success=True,
            shapes=[
                Shape(
                    type='triangle',
                    name='Triangle ABC',
                    labels=['A', 'B', 'C'],
                    sides=[
                        SideMeasurement('A', 'B', '3cm', None, False),
                        SideMeasurement('B', 'C', '4cm', None, False),
                        SideMeasurement('C', 'A', '5cm', None, False)
                    ],
                    angles=[
                        AngleMeasurement('C', '90°', None, True)
                    ],
                    properties=['right triangle']
                )
            ],
            problem_text=['Find the area'],
            given_information=['Right angle at C'],
            confidence=0.92
        )

        formatted = geometry_service.format_for_tutor(result)

        assert '[Student uploaded geometry diagram:' in formatted
        assert 'Triangle' in formatted
        assert '(Triangle ABC)' in formatted
        assert 'Side AB = 3cm' in formatted
        assert 'Side BC = 4cm' in formatted
        assert 'Angle C = 90°' in formatted
        assert 'right triangle' in formatted
        assert 'Problem: Find the area' in formatted

    def test_format_with_relationships(self, geometry_service):
        """Test formatting result with relationships."""
        from app.services.geometry_ocr_service import (
            GeometryResult, Shape, Relationship
        )

        result = GeometryResult(
            success=True,
            shapes=[
                Shape(type='line', labels=['A', 'B']),
                Shape(type='line', labels=['C', 'D'])
            ],
            relationships=[
                Relationship('parallel', ['AB', 'CD'], True)
            ],
            confidence=0.88
        )

        formatted = geometry_service.format_for_tutor(result)

        assert 'Relationships:' in formatted
        assert 'parallel' in formatted
        assert 'AB' in formatted
        assert 'CD' in formatted
        assert '(marked)' in formatted

    def test_format_with_low_confidence(self, geometry_service):
        """Test formatting with low confidence indicator."""
        from app.services.geometry_ocr_service import GeometryResult, Shape

        result = GeometryResult(
            success=True,
            shapes=[Shape(type='triangle')],
            confidence=0.65  # Low confidence
        )

        formatted = geometry_service.format_for_tutor(result)

        assert 'low confidence' in formatted
        assert '65%' in formatted

    def test_format_failed_result(self, geometry_service):
        """Test formatting failed extraction result."""
        from app.services.geometry_ocr_service import GeometryResult

        result = GeometryResult(
            success=False,
            error='Extraction failed'
        )

        formatted = geometry_service.format_for_tutor(result)

        assert 'extraction failed' in formatted.lower()


class TestGeometryShapeSummary:
    """Test get_shape_summary() method (AC-4)."""

    @pytest.fixture
    def geometry_service(self):
        """Create GeometryOCRService for testing."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            with patch('app.services.geometry_ocr_service.OpenAI'):
                from app.services.geometry_ocr_service import GeometryOCRService
                return GeometryOCRService()

    def test_shape_summary_basic(self, geometry_service):
        """Test basic shape summary generation."""
        from app.services.geometry_ocr_service import (
            GeometryResult, Shape, SideMeasurement
        )

        result = GeometryResult(
            success=True,
            shapes=[
                Shape(type='triangle', sides=[SideMeasurement('A', 'B', '5cm', None, False)]),
                Shape(type='triangle'),
                Shape(type='circle')
            ],
            relationships=[],
            problem_text=['Find the perimeter'],
            confidence=0.9
        )

        summary = geometry_service.get_shape_summary(result)

        assert summary['total_shapes'] == 3
        assert summary['shape_counts']['triangle'] == 2
        assert summary['shape_counts']['circle'] == 1
        assert summary['has_measurements'] is True
        assert summary['has_problem'] is True
        assert summary['confidence'] == 0.9

    def test_shape_summary_with_relationships(self, geometry_service):
        """Test summary with relationships."""
        from app.services.geometry_ocr_service import GeometryResult, Shape, Relationship

        result = GeometryResult(
            success=True,
            shapes=[Shape(type='line')],
            relationships=[
                Relationship('parallel', ['AB', 'CD']),
                Relationship('perpendicular', ['EF', 'GH'])
            ],
            confidence=0.85
        )

        summary = geometry_service.get_shape_summary(result)

        assert summary['has_relationships'] is True
        assert 'parallel' in summary['relationship_types']
        assert 'perpendicular' in summary['relationship_types']


class TestGeometryAPIEndpoint:
    """Test /api/images/ocr/geometry endpoint."""

    def test_geometry_endpoint_exists(self):
        """Verify geometry endpoint function exists."""
        from app.routes.images import extract_geometry
        assert callable(extract_geometry)

    def test_geometry_service_initialization(self):
        """Test geometry service can be initialized."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            with patch('app.services.geometry_ocr_service.OpenAI'):
                from app.services.geometry_ocr_service import GeometryOCRService
                service = GeometryOCRService()
                assert service is not None
                assert service.model_name == 'gpt-4o'


class TestSocraticGuardGeometry:
    """Test Socratic Guard geometry detection (AC-6)."""

    @pytest.fixture
    def socratic_guard(self):
        """Create SocraticGuard for testing."""
        with patch.dict('os.environ', {'OPENAI_API_KEY': 'test-key'}):
            with patch('app.services.socratic_guard.OpenAI'):
                from app.services.socratic_guard import SocraticGuard
                return SocraticGuard()

    def test_detect_geometry_triangle(self, socratic_guard):
        """Test detection of triangle content."""
        message = "Triangle ABC has sides 3, 4, and 5"
        assert socratic_guard._detect_geometry_content(message) is True

    def test_detect_geometry_circle(self, socratic_guard):
        """Test detection of circle content."""
        message = "Circle with radius 5cm"
        assert socratic_guard._detect_geometry_content(message) is True

    def test_detect_geometry_angle(self, socratic_guard):
        """Test detection of angle content."""
        message = "The angle measures 90 degrees"
        assert socratic_guard._detect_geometry_content(message) is True

    def test_detect_geometry_relationship(self, socratic_guard):
        """Test detection of geometric relationships."""
        message = "Lines AB and CD are parallel"
        assert socratic_guard._detect_geometry_content(message) is True

    def test_detect_geometry_perpendicular(self, socratic_guard):
        """Test detection of perpendicular relationship."""
        message = "AB is perpendicular to CD"
        assert socratic_guard._detect_geometry_content(message) is True

    def test_detect_geometry_pythagorean(self, socratic_guard):
        """Test detection of Pythagorean theorem."""
        message = "Use the Pythagorean theorem"
        assert socratic_guard._detect_geometry_content(message) is True

    def test_detect_geometry_notation(self, socratic_guard):
        """Test detection of geometry notation patterns."""
        messages = [
            "Triangle ABC",
            "Angle ABC = 45°",
            "Side AB = 5cm"
        ]
        for msg in messages:
            assert socratic_guard._detect_geometry_content(msg) is True

    def test_detect_non_geometry(self, socratic_guard):
        """Test that non-geometry content is not detected."""
        message = "Solve for x in 3x + 2 = 5"
        assert socratic_guard._detect_geometry_content(message) is False

    def test_detect_non_geometry_arithmetic(self, socratic_guard):
        """Test that arithmetic is not detected as geometry."""
        message = "What is 25 + 17?"
        assert socratic_guard._detect_geometry_content(message) is False
