"""
Módulo de base de datos.
Maneja la conexión y configuración de SQLAlchemy.
"""

from flask_sqlalchemy import SQLAlchemy

# Crear instancia de SQLAlchemy (sin app asociada inicialmente)
db = SQLAlchemy()


def init_app(app):
    """Inicializar SQLAlchemy con la aplicación Flask"""
    db.init_app(app)
    
    with app.app_context():
        # Crear tablas si no existen
        db.create_all()
        print("Base de datos inicializada correctamente")


def get_session():
    """Obtener sesión de base de datos (para usar fuera del contexto de app)"""
    from backend.app import create_app
    app = create_app()
    with app.app_context():
        return db.session