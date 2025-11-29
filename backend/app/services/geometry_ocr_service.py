"""Geometry OCR Service - Structured extraction of geometric diagrams (Story 8-5).

Provides specialized processing for geometry images, extracting:
- Shapes (triangles, circles, rectangles, polygons, lines, angles)
- Measurements (sides, angles, radii, areas)
- Labels (vertex names, variables)
- Relationships (parallel, perpendicular, congruent, similar)
- Problem text and given information
"""
import logging
import os
import re
import base64
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict
from openai import OpenAI

logger = logging.getLogger(__name__)


# Geometry-specific prompt for structured extraction (AC-1)
GEOMETRY_PROMPT = """You are analyzing a geometric diagram or shape image.
Extract ALL visible geometric information in a structured format.

STEP 1 - IDENTIFY SHAPES:
List all geometric shapes visible (triangles, circles, rectangles, squares, polygons, lines, angles).
Note any compound figures (e.g., a triangle inscribed in a circle).

STEP 2 - EXTRACT MEASUREMENTS:
For each shape, extract:
- Side lengths with units (e.g., "3cm", "5 units", "x")
- Angle measurements (e.g., "90°", "45 degrees", "y°")
- Radii/diameters for circles
- Any labeled numerical values

STEP 3 - IDENTIFY LABELS:
Extract all text labels:
- Vertex labels (A, B, C, P, Q, R, etc.)
- Variable labels (x, y, θ, etc.)
- Measurement annotations
- Shape names (e.g., "Triangle ABC")

STEP 4 - DETECT RELATIONSHIPS:
Identify geometric relationships:
- Parallel lines (look for arrow marks: >> or ||)
- Perpendicular lines (look for small squares at intersections)
- Congruent segments (look for tick marks on sides)
- Similar triangles or shapes
- Inscribed/circumscribed relationships

STEP 5 - EXTRACT PROBLEM TEXT:
Capture any questions or instructions:
- "Find x"
- "Calculate the area"
- "Prove that..."
- "What is the perimeter?"

STEP 6 - OUTPUT JSON:
{
    "shapes": [
        {
            "type": "triangle",
            "name": "Triangle ABC",
            "labels": ["A", "B", "C"],
            "sides": [
                {"from": "A", "to": "B", "length": "3cm", "variable": null},
                {"from": "B", "to": "C", "length": null, "variable": "x"},
                {"from": "C", "to": "A", "length": "5cm", "variable": null}
            ],
            "angles": [
                {"vertex": "A", "measure": "90°", "variable": null, "marked": true},
                {"vertex": "B", "measure": null, "variable": "y", "marked": false}
            ],
            "properties": ["right triangle"]
        }
    ],
    "relationships": [
        {"type": "parallel", "elements": ["AB", "CD"], "marked": true},
        {"type": "perpendicular", "elements": ["AB", "BC"], "marked": true}
    ],
    "problem_text": ["Find the value of x", "Calculate the area"],
    "given_information": ["AB = 3cm", "BC = 4cm", "Angle A = 90°"],
    "confidence": 0.85
}

IMPORTANT RULES:
- Extract ONLY what is visible - never invent measurements
- Mark unclear values as "[unclear:best_guess/alternative]"
- Mark unreadable values as "[unreadable]"
- Include tick marks on sides as congruence indicators
- Include arc marks on angles
- Confidence should reflect clarity of the diagram (0.0-1.0)

Respond ONLY with the JSON object, no additional text."""


@dataclass
class SideMeasurement:
    """Represents a side of a shape with its measurement."""
    from_point: str
    to_point: str
    length: Optional[str] = None  # "3cm", "5 units"
    variable: Optional[str] = None  # "x", "y"
    marked_congruent: bool = False


@dataclass
class AngleMeasurement:
    """Represents an angle with its measurement."""
    vertex: str
    measure: Optional[str] = None  # "90°", "45 degrees"
    variable: Optional[str] = None  # "θ", "y"
    marked: bool = False  # Has arc mark or square (right angle)


@dataclass
class Shape:
    """Represents a geometric shape extracted from a diagram (AC-3, AC-4)."""
    type: str  # triangle, circle, rectangle, square, polygon, line, angle
    name: Optional[str] = None  # "Triangle ABC"
    labels: List[str] = field(default_factory=list)  # ["A", "B", "C"]
    sides: List[SideMeasurement] = field(default_factory=list)
    angles: List[AngleMeasurement] = field(default_factory=list)
    radius: Optional[str] = None  # For circles
    diameter: Optional[str] = None  # For circles
    center: Optional[str] = None  # Center point label for circles
    area: Optional[str] = None
    perimeter: Optional[str] = None
    properties: List[str] = field(default_factory=list)  # ["right triangle", "isosceles"]


@dataclass
class Relationship:
    """Represents a geometric relationship between elements (AC-3, AC-5)."""
    type: str  # parallel, perpendicular, congruent, similar
    elements: List[str] = field(default_factory=list)  # ["AB", "CD"]
    marked: bool = False  # Whether relationship is marked on diagram


@dataclass
class GeometryResult:
    """Complete result from geometry OCR extraction (AC-3)."""
    success: bool = True
    shapes: List[Shape] = field(default_factory=list)
    relationships: List[Relationship] = field(default_factory=list)
    problem_text: List[str] = field(default_factory=list)
    given_information: List[str] = field(default_factory=list)
    raw_response: Optional[str] = None
    confidence: float = 0.0
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            'success': self.success,
            'shapes': [],
            'relationships': [],
            'problem_text': self.problem_text,
            'given_information': self.given_information,
            'confidence': self.confidence
        }

        for shape in self.shapes:
            shape_dict = {
                'type': shape.type,
                'name': shape.name,
                'labels': shape.labels,
                'sides': [
                    {
                        'from': s.from_point,
                        'to': s.to_point,
                        'length': s.length,
                        'variable': s.variable,
                        'marked_congruent': s.marked_congruent
                    } for s in shape.sides
                ],
                'angles': [
                    {
                        'vertex': a.vertex,
                        'measure': a.measure,
                        'variable': a.variable,
                        'marked': a.marked
                    } for a in shape.angles
                ],
                'radius': shape.radius,
                'diameter': shape.diameter,
                'center': shape.center,
                'area': shape.area,
                'perimeter': shape.perimeter,
                'properties': shape.properties
            }
            result['shapes'].append(shape_dict)

        for rel in self.relationships:
            result['relationships'].append({
                'type': rel.type,
                'elements': rel.elements,
                'marked': rel.marked
            })

        if self.error:
            result['error'] = self.error

        return result


class GeometryOCRService:
    """Service for structured geometry extraction from images (AC-2).

    Uses GPT-4o Vision to extract shapes, measurements, labels, and
    relationships from geometric diagrams.
    """

    def __init__(self, model_name: str = "gpt-4o"):
        """Initialize Geometry OCR service.

        Args:
            model_name: OpenAI vision model name (gpt-4o recommended)
        """
        self.model_name = model_name
        api_key = os.environ.get('OPENAI_API_KEY')

        if not api_key:
            logger.error("OPENAI_API_KEY not found in environment variables")
            raise ValueError("OPENAI_API_KEY is required for GeometryOCRService")

        self.client = OpenAI(api_key=api_key)
        logger.info(f"Initialized GeometryOCRService with model {model_name}")

    def extract(self, image_path: str) -> GeometryResult:
        """Extract structured geometry data from an image (AC-2, AC-4, AC-5).

        Args:
            image_path: Path to the geometry diagram image

        Returns:
            GeometryResult with shapes, relationships, and extracted data
        """
        try:
            logger.info(f"Extracting geometry from image: {image_path}")

            # Encode image as base64
            with open(image_path, "rb") as image_file:
                image_data = image_file.read()
                base64_image = base64.b64encode(image_data).decode('utf-8')

            # Determine image format
            image_format = image_path.split('.')[-1].lower()
            if image_format == 'jpg':
                image_format = 'jpeg'

            # Call OpenAI Vision API
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": GEOMETRY_PROMPT
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
                max_tokens=2000,
                temperature=0.0  # Deterministic output for consistent extraction
            )

            raw_response = response.choices[0].message.content.strip()
            logger.info(f"Raw geometry extraction response: {raw_response[:500]}...")

            # Parse the structured response
            result = self._parse_geometry_response(raw_response)
            result.raw_response = raw_response

            logger.info(
                f"Geometry extraction complete. "
                f"Shapes: {len(result.shapes)}, "
                f"Relationships: {len(result.relationships)}, "
                f"Confidence: {result.confidence:.2f}"
            )

            return result

        except FileNotFoundError:
            error_msg = f"Image file not found: {image_path}"
            logger.error(error_msg)
            return GeometryResult(success=False, error=error_msg, confidence=0.0)

        except Exception as e:
            error_msg = f"Geometry extraction failed: {str(e)}"
            logger.error(error_msg)
            return GeometryResult(success=False, error=error_msg, confidence=0.0)

    def _parse_geometry_response(self, raw_response: str) -> GeometryResult:
        """Parse the JSON response from GPT-4o into structured data.

        Args:
            raw_response: Raw JSON string from GPT-4o

        Returns:
            GeometryResult with parsed shapes and relationships
        """
        try:
            # Extract JSON from response
            json_match = re.search(r'\{[\s\S]*\}', raw_response)
            if not json_match:
                logger.warning("No JSON found in geometry response")
                return GeometryResult(
                    success=False,
                    error="No structured data extracted from image",
                    confidence=0.0
                )

            json_str = json_match.group()
            parsed = json.loads(json_str)

            # Parse shapes
            shapes = []
            for shape_data in parsed.get('shapes', []):
                shape = self._parse_shape(shape_data)
                shapes.append(shape)

            # Parse relationships
            relationships = []
            for rel_data in parsed.get('relationships', []):
                relationship = Relationship(
                    type=rel_data.get('type', 'unknown'),
                    elements=rel_data.get('elements', []),
                    marked=rel_data.get('marked', False)
                )
                relationships.append(relationship)

            return GeometryResult(
                success=True,
                shapes=shapes,
                relationships=relationships,
                problem_text=parsed.get('problem_text', []),
                given_information=parsed.get('given_information', []),
                confidence=float(parsed.get('confidence', 0.85))
            )

        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Failed to parse geometry JSON: {e}")
            return GeometryResult(
                success=False,
                error=f"Failed to parse geometry data: {str(e)}",
                confidence=0.0
            )

    def _parse_shape(self, shape_data: Dict[str, Any]) -> Shape:
        """Parse a single shape from JSON data (AC-4).

        Args:
            shape_data: Dictionary with shape data

        Returns:
            Shape object
        """
        # Parse sides
        sides = []
        for side_data in shape_data.get('sides', []):
            side = SideMeasurement(
                from_point=side_data.get('from', ''),
                to_point=side_data.get('to', ''),
                length=side_data.get('length'),
                variable=side_data.get('variable'),
                marked_congruent=side_data.get('marked_congruent', False)
            )
            sides.append(side)

        # Parse angles
        angles = []
        for angle_data in shape_data.get('angles', []):
            angle = AngleMeasurement(
                vertex=angle_data.get('vertex', ''),
                measure=angle_data.get('measure'),
                variable=angle_data.get('variable'),
                marked=angle_data.get('marked', False)
            )
            angles.append(angle)

        return Shape(
            type=shape_data.get('type', 'unknown'),
            name=shape_data.get('name'),
            labels=shape_data.get('labels', []),
            sides=sides,
            angles=angles,
            radius=shape_data.get('radius'),
            diameter=shape_data.get('diameter'),
            center=shape_data.get('center'),
            area=shape_data.get('area'),
            perimeter=shape_data.get('perimeter'),
            properties=shape_data.get('properties', [])
        )

    def format_for_tutor(self, result: GeometryResult) -> str:
        """Format geometry result for tutor context (AC-6).

        Produces a natural language description that the Socratic tutor
        can use to reference the geometry diagram in responses.

        Args:
            result: GeometryResult from extraction

        Returns:
            Formatted string for tutor context
        """
        if not result.success:
            return "[Geometry diagram uploaded - extraction failed]"

        parts = ["[Student uploaded geometry diagram:"]

        # Describe shapes
        for shape in result.shapes:
            shape_desc = f"  - {shape.type.capitalize()}"
            if shape.name:
                shape_desc += f" ({shape.name})"
            if shape.labels:
                shape_desc += f" with vertices {', '.join(shape.labels)}"
            if shape.properties:
                shape_desc += f" [{', '.join(shape.properties)}]"
            parts.append(shape_desc)

            # Add side measurements
            for side in shape.sides:
                if side.length:
                    parts.append(f"    Side {side.from_point}{side.to_point} = {side.length}")
                elif side.variable:
                    parts.append(f"    Side {side.from_point}{side.to_point} = {side.variable} (unknown)")

            # Add angle measurements
            for angle in shape.angles:
                if angle.measure:
                    parts.append(f"    Angle {angle.vertex} = {angle.measure}")
                elif angle.variable:
                    parts.append(f"    Angle {angle.vertex} = {angle.variable} (unknown)")

            # Circle-specific
            if shape.radius:
                parts.append(f"    Radius = {shape.radius}")
            if shape.diameter:
                parts.append(f"    Diameter = {shape.diameter}")

        # Describe relationships
        if result.relationships:
            parts.append("  Relationships:")
            for rel in result.relationships:
                rel_desc = f"    {rel.type}: {' and '.join(rel.elements)}"
                if rel.marked:
                    rel_desc += " (marked)"
                parts.append(rel_desc)

        # Add given information
        if result.given_information:
            parts.append(f"  Given: {', '.join(result.given_information)}")

        # Add problem text
        if result.problem_text:
            parts.append(f"  Problem: {', '.join(result.problem_text)}")

        # Add confidence indicator
        if result.confidence < 0.8:
            parts.append(f"  (low confidence: {result.confidence:.0%} - some elements may be unclear)")

        parts.append("]")
        return "\n".join(parts)

    def get_shape_summary(self, result: GeometryResult) -> Dict[str, Any]:
        """Get a summary of shapes for quick reference (AC-4).

        Args:
            result: GeometryResult from extraction

        Returns:
            Summary dictionary with shape counts and types
        """
        shape_counts = {}
        for shape in result.shapes:
            shape_type = shape.type
            shape_counts[shape_type] = shape_counts.get(shape_type, 0) + 1

        has_measurements = any(
            any(s.length or s.variable for s in shape.sides) or
            any(a.measure or a.variable for a in shape.angles)
            for shape in result.shapes
        )

        has_relationships = len(result.relationships) > 0
        has_problem = len(result.problem_text) > 0

        return {
            'total_shapes': len(result.shapes),
            'shape_counts': shape_counts,
            'has_measurements': has_measurements,
            'has_relationships': has_relationships,
            'has_problem': has_problem,
            'relationship_types': list(set(r.type for r in result.relationships)),
            'confidence': result.confidence
        }
