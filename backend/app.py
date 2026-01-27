"""
Punto de entrada principal de la aplicación Flask.
Configura e inicializa todos los componentes.
"""

from flask import Flask, render_template
from backend.config import config
from backend.database.db import db, init_app
from backend.routes.habits import habits_bp
import os


def create_app(config_name='default'):
    """
    Factory function para crear la aplicación Flask.
    
    Args:
        config_name: Entorno de configuración
        
    Returns:
        Flask: Aplicación configurada
    """
    # Crear aplicación Flask
    app = Flask(__name__,
                static_folder='../frontend/static',
                template_folder='../frontend/templates')
    
    # Cargar configuración
    app.config.from_object(config[config_name])
    
    # Inicializar extensiones
    init_app(app)
    
    # Registrar blueprints (rutas)
    app.register_blueprint(habits_bp)
    
    # Ruta para página de error 404
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404
    
    # Ruta para página de error 500
    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('500.html'), 500
    
    # Ruta principal redirige al dashboard
    @app.route('/')
    def home():
        return render_template('index.html')
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        return {'status': 'healthy', 'service': 'HabitIQ'}
    
    return app


if __name__ == '__main__':
    # Crear aplicación con configuración de desarrollo
    app = create_app('development')
    
    # Ejecutar servidor
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)