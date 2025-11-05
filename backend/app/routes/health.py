"""Health check endpoint."""
from datetime import datetime
from typing import Dict, Any, Tuple
from flask import Blueprint, jsonify, Response

from app.services.llm_service import get_llm_service
from app.services.sympy_service import SymPyService

health_bp = Blueprint('health', __name__, url_prefix='/api')
sympy_service = SymPyService()


@health_bp.route('/health', methods=['GET'])
def health_check() -> Tuple[Response, int]:
    """Health check endpoint.

    Returns:
        JSON response with health status and 200 status code.
        Includes LLM service health status in services.llm field.
    """
    # Check LLM service health
    llm_service = get_llm_service()
    llm_health = llm_service.check_health()

    # Check SymPy service health
    sympy_health = sympy_service.health_check()

    # Determine overall health status
    overall_status = 'healthy'
    if llm_health['status'] == 'unhealthy' or sympy_health['status'] == 'error':
        overall_status = 'degraded'
    elif llm_health['status'] == 'degraded':
        overall_status = 'degraded'

    response: Dict[str, Any] = {
        'success': True,
        'data': {
            'status': overall_status,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'services': {
                'llm': llm_health,
                'sympy': sympy_health
            }
        }
    }
    return jsonify(response), 200


@health_bp.route('/health/sympy', methods=['GET'])
def sympy_health_check() -> Tuple[Response, int]:
    """SymPy-specific health check endpoint.

    Returns:
        JSON response with SymPy health status
    """
    result = sympy_service.health_check()

    status_code = 200 if result['status'] == 'ok' else 500
    return jsonify(result), status_code
