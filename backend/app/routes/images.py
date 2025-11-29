"""Image upload and OCR routes.

Enhanced with:
- Hybrid OCR pipeline (Story 8-2): Supports method parameter (hybrid, gpt4o, pix2text)
- Redis caching (Story 8-3): Caches OCR results with image hash keys
- Geometry OCR (Story 8-5): Structured extraction of geometric diagrams
"""
import os
import logging
import hashlib
from uuid import uuid4
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from app.services.vision_service import VisionService

# Import hybrid OCR service (Story 8-2)
try:
    from app.services.hybrid_ocr_service import HybridOCRService
    HYBRID_OCR_AVAILABLE = True
except ImportError as e:
    logging.warning(f"HybridOCRService not available: {e}")
    HYBRID_OCR_AVAILABLE = False

# Import Redis service (Story 8-3)
try:
    from app.services.redis_service import get_redis_service
    REDIS_AVAILABLE = True
except ImportError as e:
    logging.warning(f"RedisService not available: {e}")
    REDIS_AVAILABLE = False

# Import Geometry OCR service (Story 8-5)
try:
    from app.services.geometry_ocr_service import GeometryOCRService
    GEOMETRY_OCR_AVAILABLE = True
except ImportError as e:
    logging.warning(f"GeometryOCRService not available: {e}")
    GEOMETRY_OCR_AVAILABLE = False

logger = logging.getLogger(__name__)

images_bp = Blueprint('images', __name__, url_prefix='/api/images')

# Initialize services
vision_service = VisionService(model_name="gpt-4o")
hybrid_service = None
if HYBRID_OCR_AVAILABLE:
    try:
        hybrid_service = HybridOCRService()
        logger.info("HybridOCRService initialized")
    except Exception as e:
        logger.warning(f"Failed to initialize HybridOCRService: {e}")

# Initialize Redis service (Story 8-3)
redis_service = None
if REDIS_AVAILABLE:
    try:
        redis_service = get_redis_service()
        logger.info(f"RedisService initialized (connected: {redis_service.is_connected()})")
    except Exception as e:
        logger.warning(f"Failed to initialize RedisService: {e}")

# Initialize Geometry OCR service (Story 8-5)
geometry_service = None
if GEOMETRY_OCR_AVAILABLE:
    try:
        geometry_service = GeometryOCRService()
        logger.info("GeometryOCRService initialized")
    except Exception as e:
        logger.warning(f"Failed to initialize GeometryOCRService: {e}")

# Configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename: str) -> bool:
    """Check if file has allowed extension.

    Args:
        filename: Name of file

    Returns:
        True if extension is allowed
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@images_bp.route('/upload', methods=['POST'])
def upload_image():
    """Upload image endpoint.

    Accepts multipart/form-data with 'image' field.
    Returns image_id and URL for further processing.
    """
    try:
        # Check if image file is present
        if 'image' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No image file provided'
            }), 400

        file = request.files['image']

        # Check if file is selected
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400

        # Validate file type
        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'error': 'Unsupported format. Please use PNG, JPG, or WEBP.'
            }), 400

        # Check file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)

        if file_size > MAX_FILE_SIZE:
            return jsonify({
                'success': False,
                'error': 'Image too large. Maximum size is 5MB.'
            }), 400

        # Generate unique filename
        image_id = str(uuid4())
        extension = file.filename.rsplit('.', 1)[1].lower()
        filename = f"{image_id}.{extension}"
        filepath = os.path.join(UPLOAD_FOLDER, filename)

        # Save file
        file.save(filepath)
        logger.info(f"Saved uploaded image: {filename}")

        # Return image info
        return jsonify({
            'success': True,
            'image_id': image_id,
            'filename': filename,
            'url': f'/api/images/{image_id}'
        }), 200

    except Exception as e:
        logger.error(f"Error uploading image: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to upload image'
        }), 500


@images_bp.route('/ocr/extract', methods=['POST'])
def extract_ocr():
    """Extract text from uploaded image using OCR.

    Accepts JSON with image_id (and optional subject, method) or multipart/form-data with image file.

    Query Parameters (Story 8-2):
        method: OCR method to use - 'hybrid' (default), 'gpt4o', 'pix2text'

    Returns:
        JSON with extracted text, latex, confidence, problem_type, method_used, and math_detected flag.
    """
    try:
        image_path = None
        subject = None
        method = request.args.get('method', 'hybrid')  # Default to hybrid (Story 8-2)

        # Validate method parameter
        valid_methods = ['hybrid', 'gpt4o', 'pix2text']
        if method not in valid_methods:
            return jsonify({
                'success': False,
                'error': f"Invalid method '{method}'. Valid methods: {valid_methods}"
            }), 400

        # Check if image_id is provided (for already uploaded images)
        if request.is_json:
            data = request.get_json()
            image_id = data.get('image_id')
            subject = data.get('subject')  # Optional: 'algebra', 'geometry', 'arithmetic'
            # Method can also be passed in JSON body
            if 'method' in data:
                method = data.get('method', method)

            if not image_id:
                return jsonify({
                    'success': False,
                    'error': 'No image_id provided'
                }), 400

            # Find image file
            for ext in ALLOWED_EXTENSIONS:
                filepath = os.path.join(UPLOAD_FOLDER, f"{image_id}.{ext}")
                if os.path.exists(filepath):
                    image_path = filepath
                    break

            if not image_path:
                return jsonify({
                    'success': False,
                    'error': 'Image not found'
                }), 404

        # Or accept direct image upload
        elif 'image' in request.files:
            file = request.files['image']
            subject = request.form.get('subject')  # Get subject from form data

            if file.filename == '' or not allowed_file(file.filename):
                return jsonify({
                    'success': False,
                    'error': 'Invalid image file'
                }), 400

            # Save temporarily
            image_id = str(uuid4())
            extension = file.filename.rsplit('.', 1)[1].lower()
            filename = f"{image_id}.{extension}"
            image_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(image_path)

        else:
            return jsonify({
                'success': False,
                'error': 'No image provided'
            }), 400

        # Calculate image hash for caching (Story 8-3)
        image_hash = None
        if image_path:
            try:
                with open(image_path, 'rb') as f:
                    image_hash = hashlib.md5(f.read()).hexdigest()[:8]
                logger.info(f"Image hash: {image_hash}")
            except Exception as e:
                logger.warning(f"Failed to calculate image hash: {e}")

        # Check cache first (Story 8-3, AC-3)
        if redis_service and redis_service.is_connected() and image_hash:
            cached_result = redis_service.get_cached_ocr(image_hash, subject)
            if cached_result:
                logger.info(f"Returning cached OCR result for {image_hash}")
                return jsonify(cached_result), 200

        # Process with OCR using appropriate service (Story 8-2)
        logger.info(f"Processing OCR for image: {image_path}, subject: {subject}, method: {method}")

        # Route to hybrid service if available and requested
        if method in ['hybrid', 'pix2text'] and hybrid_service is not None:
            result = hybrid_service.extract(image_path, subject=subject, method=method)
        else:
            # Fall back to vision service (gpt4o-only mode)
            result = vision_service.extract_text_from_image(image_path, subject=subject)
            result['method_used'] = 'gpt4o'

        if not result.get('success', False):
            return jsonify(result), 500

        # Cache successful result (Story 8-3, AC-3)
        if redis_service and redis_service.is_connected() and image_hash and result.get('success'):
            redis_service.cache_ocr_result(image_hash, result, subject)
            result['cached'] = False  # Mark as fresh result

        return jsonify(result), 200

    except Exception as e:
        logger.error(f"Error during OCR extraction: {e}")
        return jsonify({
            'success': False,
            'error': 'OCR processing failed'
        }), 500


@images_bp.route('/ocr/methods', methods=['GET'])
def get_ocr_methods():
    """Get available OCR methods and their status (Story 8-2).

    Returns:
        JSON with available methods and recommended default.
    """
    if hybrid_service is not None:
        status = hybrid_service.check_availability()
    else:
        status = {
            'hybrid_available': False,
            'pix2text_available': False,
            'gpt4o_available': True,
            'recommended_method': 'gpt4o'
        }

    return jsonify({
        'success': True,
        'methods': ['hybrid', 'gpt4o', 'pix2text'],
        'availability': status
    }), 200


@images_bp.route('/ocr/cache/<image_hash>', methods=['DELETE'])
def invalidate_ocr_cache(image_hash: str):
    """Invalidate cached OCR result for an image (Story 8-3, AC-5).

    Args:
        image_hash: MD5 hash (8 chars) of the image to invalidate

    Returns:
        JSON with number of keys deleted
    """
    try:
        if not redis_service or not redis_service.is_connected():
            return jsonify({
                'success': False,
                'error': 'Cache service not available'
            }), 503

        # Validate hash format (should be 8 hex characters)
        if not image_hash or len(image_hash) != 8:
            return jsonify({
                'success': False,
                'error': 'Invalid image hash format. Expected 8 character hex string.'
            }), 400

        keys_deleted = redis_service.invalidate_ocr_cache(image_hash)

        return jsonify({
            'success': True,
            'data': {
                'image_hash': image_hash,
                'keys_deleted': keys_deleted
            }
        }), 200

    except Exception as e:
        logger.error(f"Error invalidating cache: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to invalidate cache'
        }), 500


@images_bp.route('/ocr/cache/stats', methods=['GET'])
def get_cache_stats():
    """Get OCR cache statistics (Story 8-3, AC-7).

    Returns:
        JSON with cache metrics for monitoring
    """
    try:
        if not redis_service:
            return jsonify({
                'success': True,
                'data': {
                    'status': 'disabled',
                    'redis_available': False
                }
            }), 200

        stats = redis_service.get_cache_stats()
        health = redis_service.health_check()

        return jsonify({
            'success': True,
            'data': {
                **stats,
                'health': health
            }
        }), 200

    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve cache statistics'
        }), 500


@images_bp.route('/ocr/geometry', methods=['POST'])
def extract_geometry():
    """Extract structured geometry data from an image (Story 8-5, AC-2).

    Specialized endpoint for processing geometric diagrams, extracting:
    - Shapes (triangles, circles, rectangles, polygons, lines, angles)
    - Measurements (sides, angles, radii, areas)
    - Labels (vertex names, variables)
    - Relationships (parallel, perpendicular, congruent, similar)
    - Problem text and given information

    Accepts JSON with image_id or multipart/form-data with image file.

    Returns:
        JSON with structured geometry data (shapes, relationships, etc.)
    """
    try:
        # Check if geometry service is available
        if not geometry_service:
            return jsonify({
                'success': False,
                'error': 'Geometry OCR service not available'
            }), 503

        image_path = None

        # Check if image_id is provided (for already uploaded images)
        if request.is_json:
            data = request.get_json()
            image_id = data.get('image_id')

            if not image_id:
                return jsonify({
                    'success': False,
                    'error': 'No image_id provided'
                }), 400

            # Find image file
            for ext in ALLOWED_EXTENSIONS:
                filepath = os.path.join(UPLOAD_FOLDER, f"{image_id}.{ext}")
                if os.path.exists(filepath):
                    image_path = filepath
                    break

            if not image_path:
                return jsonify({
                    'success': False,
                    'error': 'Image not found'
                }), 404

        # Or accept direct image upload
        elif 'image' in request.files:
            file = request.files['image']

            if file.filename == '' or not allowed_file(file.filename):
                return jsonify({
                    'success': False,
                    'error': 'Invalid image file'
                }), 400

            # Save temporarily
            image_id = str(uuid4())
            extension = file.filename.rsplit('.', 1)[1].lower()
            filename = f"{image_id}.{extension}"
            image_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(image_path)
            logger.info(f"Saved geometry image: {filename}")

        else:
            return jsonify({
                'success': False,
                'error': 'No image provided'
            }), 400

        # Calculate image hash for caching
        image_hash = None
        if image_path:
            try:
                with open(image_path, 'rb') as f:
                    image_hash = hashlib.md5(f.read()).hexdigest()[:8]
                logger.info(f"Geometry image hash: {image_hash}")
            except Exception as e:
                logger.warning(f"Failed to calculate image hash: {e}")

        # Check cache first (reuse OCR cache with geometry subject)
        if redis_service and redis_service.is_connected() and image_hash:
            cached_result = redis_service.get_cached_ocr(image_hash, 'geometry')
            if cached_result and cached_result.get('shapes'):
                logger.info(f"Returning cached geometry result for {image_hash}")
                return jsonify(cached_result), 200

        # Extract structured geometry data
        logger.info(f"Processing geometry extraction for image: {image_path}")
        result = geometry_service.extract(image_path)

        if not result.success:
            return jsonify({
                'success': False,
                'error': result.error or 'Geometry extraction failed'
            }), 500

        # Convert to dict for JSON serialization
        response_data = result.to_dict()
        response_data['image_id'] = image_id if 'image_id' in dir() else None
        response_data['image_hash'] = image_hash

        # Get shape summary for quick reference
        response_data['summary'] = geometry_service.get_shape_summary(result)

        # Get formatted context for tutor
        response_data['tutor_context'] = geometry_service.format_for_tutor(result)

        # Cache the result
        if redis_service and redis_service.is_connected() and image_hash and result.success:
            redis_service.cache_ocr_result(image_hash, response_data, 'geometry')
            response_data['cached'] = False

        return jsonify(response_data), 200

    except Exception as e:
        logger.error(f"Error during geometry extraction: {e}")
        return jsonify({
            'success': False,
            'error': 'Geometry processing failed'
        }), 500


@images_bp.route('/message/with-image', methods=['POST'])
def create_message_with_image():
    """Create a message with an uploaded image and automatic OCR (Story 8-4, AC-2).

    Unified endpoint for uploading an image and creating a message in one request.
    Automatically processes OCR and stores results in message metadata.

    Accepts multipart/form-data with:
        - conversation_id: UUID of conversation (required)
        - image: Image file (required)
        - text: Optional message text
        - subject: Optional subject hint for OCR ('algebra', 'geometry', 'arithmetic')

    Returns:
        JSON with message_id, image_id, ocr_result, and combined response
    """
    try:
        # Import required models
        from app.models import Message, Conversation, MessageRole
        from app.extensions import db

        # Validate conversation_id
        conversation_id = request.form.get('conversation_id')
        if not conversation_id:
            return jsonify({
                'success': False,
                'error': 'conversation_id is required'
            }), 400

        # Validate image file
        if 'image' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No image file provided'
            }), 400

        file = request.files['image']
        if file.filename == '' or not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'error': 'Invalid image file. Supported formats: PNG, JPG, WEBP'
            }), 400

        # Get optional parameters
        text = request.form.get('text', '')
        subject = request.form.get('subject')

        # Save image file
        image_id = str(uuid4())
        extension = file.filename.rsplit('.', 1)[1].lower()
        filename = f"{image_id}.{extension}"
        image_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(image_path)
        logger.info(f"Saved image for message: {filename}")

        # Process OCR
        ocr_method = request.form.get('method', 'hybrid')

        # Calculate image hash for caching
        with open(image_path, 'rb') as f:
            image_hash = hashlib.md5(f.read()).hexdigest()[:8]

        # Check cache first
        ocr_result = None
        if redis_service and redis_service.is_connected():
            ocr_result = redis_service.get_cached_ocr(image_hash, subject)

        if not ocr_result:
            # Route to appropriate OCR service
            if ocr_method in ['hybrid', 'pix2text'] and hybrid_service is not None:
                ocr_result = hybrid_service.extract(image_path, subject=subject, method=ocr_method)
            else:
                ocr_result = vision_service.extract_text_from_image(image_path, subject=subject)
                ocr_result['method_used'] = 'gpt4o'

            # Cache result
            if redis_service and redis_service.is_connected() and ocr_result.get('success'):
                redis_service.cache_ocr_result(image_hash, ocr_result, subject)

        # Build message content
        message_content = text if text else ocr_result.get('extracted_text', '')

        # Build message metadata with OCR data (AC-1)
        message_metadata = {
            'image_id': image_id,
            'image_path': f'/api/images/{image_id}',
            'ocr_result': ocr_result.get('extracted_text', ''),
            'ocr_latex': ocr_result.get('latex', ''),
            'ocr_confidence': ocr_result.get('confidence', 0.0),
            'ocr_method': ocr_result.get('method_used', 'gpt4o'),
            'problem_type': ocr_result.get('problem_type', 'unknown'),
            'uncertain_regions': ocr_result.get('uncertain_regions', [])
        }

        # Create message with metadata (AC-1)
        try:
            message = Message(
                conversation_id=conversation_id,
                role=MessageRole.STUDENT,
                content=message_content,
                message_metadata=message_metadata
            )
            db.session.add(message)
            db.session.commit()

            logger.info(f"Created message {message.id} with image {image_id}")

            return jsonify({
                'success': True,
                'data': {
                    'message_id': str(message.id),
                    'image_id': image_id,
                    'image_path': f'/api/images/{image_id}',
                    'ocr_result': ocr_result.get('extracted_text', ''),
                    'ocr_latex': ocr_result.get('latex', ''),
                    'ocr_confidence': ocr_result.get('confidence', 0.0),
                    'ocr_method': ocr_result.get('method_used', 'gpt4o'),
                    'problem_type': ocr_result.get('problem_type', 'unknown'),
                    'message': message.to_dict()
                }
            }), 201

        except Exception as db_error:
            logger.error(f"Database error creating message: {db_error}")
            # Clean up uploaded file on failure
            if os.path.exists(image_path):
                os.remove(image_path)
            return jsonify({
                'success': False,
                'error': 'Failed to create message'
            }), 500

    except Exception as e:
        logger.error(f"Error creating message with image: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to process image and create message'
        }), 500


@images_bp.route('/<image_id>', methods=['GET'])
def get_image(image_id: str):
    """Retrieve uploaded image by ID.

    Args:
        image_id: UUID of uploaded image

    Returns:
        Image file
    """
    try:
        # Find image file with any allowed extension
        for ext in ALLOWED_EXTENSIONS:
            filepath = os.path.join(UPLOAD_FOLDER, f"{image_id}.{ext}")
            if os.path.exists(filepath):
                from flask import send_file
                return send_file(filepath, mimetype=f'image/{ext}')

        return jsonify({
            'success': False,
            'error': 'Image not found'
        }), 404

    except Exception as e:
        logger.error(f"Error retrieving image: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve image'
        }), 500
