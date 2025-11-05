"""Flask application configuration."""
import os
from typing import Type


class Config:
    """Base configuration."""

    SECRET_KEY: str = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    CORS_ORIGINS: str = os.environ.get('CORS_ORIGINS', 'http://localhost:5173')

    # Database configuration
    SQLALCHEMY_DATABASE_URI: str = os.environ.get(
        'DATABASE_URL',
        'postgresql://supertutors:devpassword@localhost:5432/supertutors_dev'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    SQLALCHEMY_ENGINE_OPTIONS: dict = {
        'pool_size': 20,
        'max_overflow': 10,
        'pool_timeout': 30,
        'pool_pre_ping': True
    }


class DevelopmentConfig(Config):
    """Development configuration."""

    DEBUG: bool = True
    ENV: str = 'development'


class ProductionConfig(Config):
    """Production configuration."""

    DEBUG: bool = False
    ENV: str = 'production'


def get_config() -> Type[Config]:
    """Get configuration based on environment."""
    env: str = os.environ.get('FLASK_ENV', 'development')
    if env == 'production':
        return ProductionConfig
    return DevelopmentConfig
