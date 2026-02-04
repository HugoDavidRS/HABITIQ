@echo off
chcp 65001 > nul
title Instalador HabitIQ - Windows

echo.
echo ========================================================
echo              🚀 INSTALADOR DE HABITIQ
echo ========================================================
echo.

echo 🔍 Verificando Python 3.9+...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ ERROR: Python no encontrado
    echo.
    echo Por favor, instala Python 3.9 o superior:
    echo https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

echo ✅ Python detectado correctamente
echo.

echo 📦 Leyendo dependencias de requirements.txt...
if not exist "requirements.txt" (
    echo ❌ ERROR: requirements.txt no encontrado
    pause
    exit /b 1
)

echo ✅ Encontradas dependencias
echo.

echo 🔧 Creando entorno virtual...
if exist "venv" (
    echo ⚠️  El entorno virtual ya existe
    echo ¿Deseas recrearlo? (S/N)
    set /p RECREATE=
    if /i "%RECREATE%"=="S" (
        rmdir /s /q venv
        python -m venv venv
        echo ✅ Entorno virtual recreado
    ) else (
        echo ✅ Usando entorno virtual existente
    )
) else (
    python -m venv venv
    echo ✅ Entorno virtual creado
)

echo.
echo ⚡ Activando entorno virtual...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ❌ ERROR: No se pudo activar el entorno virtual
    pause
    exit /b 1
)

echo ✅ Entorno virtual activado
echo.

echo 📥 Actualizando pip...
python -m pip install --upgrade pip
echo ✅ Pip actualizado
echo.

echo 📦 Instalando dependencias principales...
echo --------------------------------------------------------
pip install Flask==2.3.3 Flask-SQLAlchemy==3.0.5 Flask-WTF==1.1.1
if errorlevel 1 (
    echo ❌ ERROR: Falló la instalación de dependencias principales
    pause
    exit /b 1
)

echo ✅ Dependencias principales instaladas
echo.

echo 🔌 Instalando dependencias adicionales...
echo --------------------------------------------------------
pip install -r requirements.txt
if errorlevel 1 (
    echo ⚠️  ADVERTENCIA: Algunas dependencias opcionales fallaron
    echo Continuando con instalación básica...
) else (
    echo ✅ Todas las dependencias instaladas
)

echo.
echo 📊 Mostrando paquetes instalados...
echo --------------------------------------------------------
pip list
echo --------------------------------------------------------
echo.

echo 🗄️  Configurando base de datos...
if not exist "backend\database" mkdir backend\database
if not exist "scripts\init_db.py" (
    echo ⚠️  Script de base de datos no encontrado
    echo Creando estructura básica...
    python -c "
import sys
sys.path.append('backend')
from app import create_app
from database.db import db

app = create_app()
with app.app_context():
    db.create_all()
    print('✅ Base de datos inicializada')
"
) else (
    python scripts\init_db.py
)

echo.
echo 🌐 Configurando archivo de entorno...
if not exist ".env" (
    echo Creando archivo .env...
    (
        echo # Configuración de HabitIQ
        echo FLASK_APP=backend/app.py
        echo FLASK_ENV=development
        echo SECRET_KEY=clave-secreta-desarrollo-cambiar-en-produccion
        echo DATABASE_URL=sqlite:///backend/database/habits.db
    ) > .env
    echo ✅ Archivo .env creado
) else (
    echo ✅ Archivo .env ya existe
)

echo.
echo ========================================================
echo                    ✅ INSTALACIÓN COMPLETADA
echo ========================================================
echo.
echo 📋 PASOS PARA EJECUTAR:
echo.
echo 1. Activar entorno virtual:
echo    venv\Scripts\activate
echo.
echo 2. Ejecutar la aplicación:
echo    python backend\app.py
echo.
echo 3. Abrir en navegador:
echo    http://localhost:5000
echo.
echo 📝 COMANDOS ÚTILES:
echo.
echo • Tests: python -m pytest tests\
echo • Reiniciar DB: python scripts\init_db.py clear
echo • Ver dependencias: pip list
echo • Desactivar entorno: deactivate
echo.
echo ========================================================
echo           🎯 ¡HabitIQ está listo para usar!
echo ========================================================
echo.
pause