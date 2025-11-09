"""Image upload and OCR routes."""
import os
import logging
from uuid import uuid4
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from app.services.vision_service import VisionService

logger = logging.getLogger(__name__)

images_bp = Blueprint('images', __name__, url_prefix='/api/images')
# Using gpt-4o (gpt-4-vision-preview is deprecated)
vision_service = VisionService(model_name="gpt-4o")

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

    Accepts JSON with image_id (and optional subject) or multipart/form-data with image file.
    Returns extracted text, confidence, and math detection flag.
    """
    try:
        image_path = None
        subject = None

        # Check if image_id is provided (for already uploaded images)
        if request.is_json:
            data = request.get_json()
            image_id = data.get('image_id')
            subject = data.get('subject')  # Optional: 'algebra', 'geometry', 'arithmetic'

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

        else:
            return jsonify({
                'success': False,
                'error': 'No image provided'
            }), 400

        # Process with OCR
        logger.info(f"Processing OCR for image: {image_path}, subject: {subject}")
        result = vision_service.extract_text_from_image(image_path, subject=subject)

        if not result['success']:
            return jsonify(result), 500

        return jsonify(result), 200

    except Exception as e:
        logger.error(f"Error during OCR extraction: {e}")
        return jsonify({
            'success': False,
            'error': 'OCR processing failed'
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
