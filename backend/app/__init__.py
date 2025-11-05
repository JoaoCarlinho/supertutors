"""Flask application factory."""
import os
import logging
import time
from typing import Optional, Any
from flask import Flask, request, g
from dotenv import load_dotenv

from app.config import get_config
from app.extensions import socketio, cors, db
from app.utils.errors import AppError, create_error_response, ErrorCodes


def configure_logging(app: Flask) -> None:
    """Configure structured logging for the application.

    Args:
        app: Flask application instance
    """
    # Determine log level from config
    log_level = logging.DEBUG if app.config.get('DEBUG') else logging.INFO

    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Set Flask logger level
    app.logger.setLevel(log_level)

    # Log startup message
    app.logger.info(
        f"Application starting - Environment: {app.config.get('ENV', 'unknown')}, "
        f"Debug: {app.config.get('DEBUG', False)}"
    )


def register_error_handlers(app: Flask) -> None:
    """Register global error handlers.

    Args:
        app: Flask application instance
    """

    @app.errorhandler(AppError)
    def handle_app_error(error: AppError) -> Any:
        """Handle application errors."""
        app.logger.error(
            f"AppError: {error.message} (code: {error.code})",
            exc_info=True
        )
        return error.to_response()

    @app.errorhandler(404)
    def handle_not_found(error: Any) -> Any:
        """Handle 404 Not Found errors."""
        return create_error_response(
            "The requested resource was not found",
            ErrorCodes.NOT_FOUND,
            404
        )

    @app.errorhandler(500)
    def handle_internal_error(error: Any) -> Any:
        """Handle 500 Internal Server Error."""
        app.logger.error("Internal server error", exc_info=True)
        return create_error_response(
            "An internal server error occurred. Please try again later.",
            ErrorCodes.INTERNAL_ERROR,
            500
        )

    @app.errorhandler(Exception)
    def handle_unhandled_exception(error: Exception) -> Any:
        """Handle unhandled exceptions."""
        app.logger.error(f"Unhandled exception: {str(error)}", exc_info=True)
        return create_error_response(
            "An unexpected error occurred. Please try again later.",
            ErrorCodes.INTERNAL_ERROR,
            500
        )


def register_middleware(app: Flask) -> None:
    """Register request/response middleware.

    Args:
        app: Flask application instance
    """

    @app.before_request
    def before_request() -> None:
        """Log request and set request start time."""
        g.start_time = time.time()

        # Skip logging for health check to reduce noise
        if request.path == '/api/health':
            return

        app.logger.info(
            f"Request: {request.method} {request.path} "
            f"from {request.remote_addr}"
        )

    @app.after_request
    def after_request(response: Any) -> Any:
        """Log response."""
        # Skip logging for health check
        if request.path == '/api/health':
            return response

        duration = time.time() - g.get('start_time', time.time())

        app.logger.info(
            f"Response: {request.method} {request.path} "
            f"status={response.status_code} duration={duration:.3f}s"
        )

        return response


def create_app(config_class: Optional[type] = None) -> Flask:
    """Create and configure the Flask application.

    Args:
        config_class: Configuration class to use. If None, uses environment-based config.

    Returns:
        Configured Flask application instance.
    """
    # Load environment variables
    load_dotenv()

    # Create Flask app
    app = Flask(__name__)

    # Load configuration
    if config_class is None:
        config_class = get_config()
    app.config.from_object(config_class)

    # Configure logging
    configure_logging(app)

    # Register error handlers
    register_error_handlers(app)

    # Register middleware
    register_middleware(app)

    # Initialize extensions
    cors.init_app(
        app,
        origins=app.config['CORS_ORIGINS'].split(','),
        supports_credentials=False,
        methods=['GET', 'POST', 'PUT', 'DELETE']
    )

    socketio.init_app(
        app,
        cors_allowed_origins=app.config['CORS_ORIGINS'].split(','),
        async_mode='eventlet'
    )

    db.init_app(app)

    # Register blueprints
    from app.routes import health, threads, images
    app.register_blueprint(health.health_bp)
    app.register_blueprint(threads.threads_bp)
    app.register_blueprint(images.images_bp)

    # Register SocketIO event handlers
    from app.routes import socket_events  # noqa: F401

    return app
