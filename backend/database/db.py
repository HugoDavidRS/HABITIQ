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

    # Intentar crear tablas al iniciar, pero no fallar si la base de datos
    # no está accesible (p. ej. problemas DNS/Red). Se captura la excepción
    # para que la aplicación pueda arrancar y el problema de conexión se
    # maneje en tiempo de ejecución.
    try:
        with app.app_context():
            db.create_all()
            print("Base de datos inicializada correctamente")
    except Exception as e:
        # Mostrar advertencia pero no detener el arranque
        print("⚠️ No se pudo crear/abrir la base de datos en init_app:", str(e))
        print("La aplicación seguirá corriendo; revisa la conexión a la DB.")


def get_session():
    """Obtener sesión de base de datos (para usar fuera del contexto de app)"""
    from backend.app import create_app
    app = create_app()
    with app.app_context():
        return db.session