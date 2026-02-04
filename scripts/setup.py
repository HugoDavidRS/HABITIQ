#!/usr/bin/env python3
"""
Script de configuración automática para HabitIQ.
Instala dependencias, configura entorno e inicializa base de datos.
"""

import os
import sys
import subprocess
import venv
from pathlib import Path


class HabitIQSetup:
    """Clase para manejar la configuración del proyecto"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.venv_path = self.project_root / 'venv'
    
    def check_python_version(self):
        """Verificar versión de Python"""
        print("🔍 Verificando versión de Python...")
        
        if sys.version_info < (3, 9):
            print(f"❌ Python 3.9+ requerido. Versión actual: {sys.version}")
            print("Por favor, actualiza Python: https://www.python.org/downloads/")
            sys.exit(1)
        
        print(f"✅ Python {sys.version} detectado")
        return True
    
    def create_virtualenv(self):
        """Crear entorno virtual"""
        print("\n🔧 Creando entorno virtual...")
        
        if self.venv_path.exists():
            print(f"✅ Entorno virtual ya existe en: {self.venv_path}")
            return True
        
        try:
            venv.create(self.venv_path, with_pip=True)
            print(f"✅ Entorno virtual creado en: {self.venv_path}")
            return True
        except Exception as e:
            print(f"❌ Error creando entorno virtual: {e}")
            return False
    
    def get_pip_path(self):
        """Obtener ruta al pip del entorno virtual"""
        if sys.platform == "win32":
            pip_path = self.venv_path / "Scripts" / "pip"
        else:
            pip_path = self.venv_path / "bin" / "pip"
        
        return str(pip_path)
    
    def install_dependencies(self):
        """Instalar dependencias desde requirements.txt"""
        print("\n📦 Instalando dependencias...")
        
        requirements_file = self.project_root / "requirements.txt"
        if not requirements_file.exists():
            print(f"❌ Archivo {requirements_file} no encontrado")
            return False
        
        pip_path = self.get_pip_path()
        
        try:
            # Actualizar pip primero
            subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], 
                         check=True, capture_output=True)
            
            # Instalar dependencias
            print(f"Usando pip en: {pip_path}")
            result = subprocess.run(
                [pip_path, "install", "-r", str(requirements_file)],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print("✅ Dependencias instaladas correctamente")
                
                # Mostrar paquetes instalados
                print("\n📊 Paquetes instalados:")
                subprocess.run([pip_path, "list"], check=True)
                return True
            else:
                print(f"❌ Error instalando dependencias: {result.stderr}")
                return False
                
        except subprocess.CalledProcessError as e:
            print(f"❌ Error en subproceso: {e}")
            return False
        except Exception as e:
            print(f"❌ Error inesperado: {e}")
            return False
    
    def create_env_file(self):
        """Crear archivo .env con variables de entorno"""
        print("\n⚙️  Configurando variables de entorno...")
        
        env_file = self.project_root / ".env"
        env_example = self.project_root / ".env.example"
        
        if env_file.exists():
            print("✅ Archivo .env ya existe")
            return True
        
        # Crear archivo .env.example si no existe
        if not env_example.exists():
            with open(env_example, 'w') as f:
                f.write("""# Configuración de HabitIQ
FLASK_APP=backend/app.py
FLASK_ENV=development
SECRET_KEY=dev-secret-key-change-in-production
DATABASE_URL=sqlite:///backend/database/habits.db

# Configuración de producción (descomentar cuando sea necesario)
# FLASK_ENV=production
# DATABASE_URL=postgresql://user:password@localhost/habitiq
""")
        
        # Copiar .env.example a .env
        import shutil
        shutil.copy2(env_example, env_file)
        print(f"✅ Archivo .env creado desde .env.example")
        return True
    
    def setup_database(self):
        """Inicializar base de datos"""
        print("\n🗄️  Inicializando base de datos...")
        
        # Asegurarse de que el directorio de base de datos existe
        db_dir = self.project_root / "backend" / "database"
        db_dir.mkdir(exist_ok=True)
        
        try:
            # Ejecutar script de inicialización
            init_script = self.project_root / "scripts" / "init_db.py"
            subprocess.run([sys.executable, str(init_script)], check=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Error inicializando base de datos: {e}")
            return False
    
    def verify_installation(self):
        """Verificar que la instalación fue exitosa"""
        print("\n🔍 Verificando instalación...")
        
        checks = [
            ("Entorno virtual", self.venv_path.exists()),
            ("Requirements", (self.project_root / "requirements.txt").exists()),
            ("Archivo .env", (self.project_root / ".env").exists()),
            ("Backend app", (self.project_root / "backend" / "app.py").exists()),
            ("Base de datos", (self.project_root / "backend" / "database" / "habits.db").exists()),
        ]
        
        all_ok = True
        for check_name, exists in checks:
            status = "✅" if exists else "❌"
            print(f"  {status} {check_name}")
            if not exists:
                all_ok = False
        
        return all_ok
    
    def print_usage_instructions(self):
        """Mostrar instrucciones de uso"""
        print("\n" + "="*60)
        print("🚀 HABITIQ - INSTALACIÓN COMPLETADA")
        print("="*60)
        
        if sys.platform == "win32":
            activate_cmd = "venv\\Scripts\\activate"
        else:
            activate_cmd = "source venv/bin/activate"
        
        print(f"""
📋 INSTRUCCIONES DE USO:

1. Activar entorno virtual:
   $ {activate_cmd}

2. Ejecutar la aplicación:
   $ python backend/app.py

3. Acceder en el navegador:
   🌐 http://localhost:5000

4. Comandos útiles:
   • Tests: python -m pytest tests/
   • Reiniciar DB: python scripts/init_db.py clear
   • Ver dependencias: pip list

📁 ESTRUCTURA DEL PROYECTO:
   • backend/    - Código del servidor
   • frontend/   - Templates y estáticos
   • tests/      - Pruebas unitarias
   • scripts/    - Scripts de utilidad
   • docs/       - Documentación

🆘 SOPORTE:
   • Revisa docs/ para documentación técnica
   • Ejecuta tests para verificar funcionamiento
   • Reporta issues en el repositorio

✅ ¡Listo para desarrollar hábitos saludables!
""")
    
    def run(self):
        """Ejecutar proceso completo de instalación"""
        print("="*60)
        print("🛠️  CONFIGURACIÓN DE HABITIQ")
        print("="*60)
        
        # Ejecutar pasos secuencialmente
        steps = [
            ("Verificar Python", self.check_python_version),
            ("Crear entorno virtual", self.create_virtualenv),
            ("Instalar dependencias", self.install_dependencies),
            ("Configurar variables", self.create_env_file),
            ("Inicializar base de datos", self.setup_database),
        ]
        
        for step_name, step_func in steps:
            print(f"\n▶️  {step_name}...")
            if not step_func():
                print(f"❌ Falló en: {step_name}")
                sys.exit(1)
        
        # Verificar instalación
        if self.verify_installation():
            self.print_usage_instructions()
        else:
            print("\n⚠️  Algunos componentes pueden necesitar configuración manual")
            self.print_usage_instructions()


if __name__ == "__main__":
    setup = HabitIQSetup()
    setup.run()