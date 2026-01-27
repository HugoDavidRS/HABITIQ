"""
Configuración de la aplicación Flask.
Define settings para desarrollo, testing y producción.
"""

import os
from pathlib import Path

# Configuración base
BASE_DIR = Path(__file__).resolve().parent.parent


class Config:
    """Configuración base para todos los entornos"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DEBUG = False
    TESTING = False
    
    # Rutas estáticas y templates
    STATIC_FOLDER = str(BASE_DIR / 'frontend/static')
    TEMPLATE_FOLDER = str(BASE_DIR / 'frontend/templates')


class DevelopmentConfig(Config):
    """Configuración para desarrollo"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + str(BASE_DIR / 'backend/database/habits.db')


class TestingConfig(Config):
    """Configuración para testing"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'  # Base de datos en memoria


class ProductionConfig(Config):
    """Configuración para producción"""
    # En producción, usar variables de entorno
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + str(BASE_DIR / 'backend/database/habits.db')
    
    if SQLALCHEMY_DATABASE_URI.startswith('postgres://'):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace('postgres://', 'postgresql://', 1)


# Configuración por defecto
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}