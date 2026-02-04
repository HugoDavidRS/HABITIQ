# Instalación de HabitIQ ✅

Guía rápida para poner en marcha el proyecto localmente.

## Requisitos previos

- Python 3.10+ instalado y accesible desde la terminal
- Git (opcional) para clonar el repositorio

## Instalación en Windows (recomendado)

1. Abrir PowerShell o CMD en la raíz del proyecto.
2. Ejecutar el script automático:

   ```
   install.bat
   ```

   Esto crea un entorno virtual `venv`, actualiza pip, instala dependencias desde `requirements.txt` y ejecuta `scripts/init_db.py` para inicializar la base de datos.

3. Activar el entorno virtual si no está activo:

   ```
   call venv\Scripts\activate.bat
   ```

4. Ejecutar la aplicación:

   ```
   python backend\app.py
   ```

   La aplicación estará disponible en http://127.0.0.1:5000

## Instalación en macOS / Linux

1. Crear y activar un entorno virtual:

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. Instalar dependencias:

   ```bash
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   ```

3. Inicializar la base de datos:

   ```bash
   python scripts/init_db.py
   ```

4. Ejecutar la aplicación:

   ```bash
   python backend/app.py
   ```

## Notas adicionales 🔧

- Si ya existe un archivo `requirements.txt`, el script `install.bat` lo usa tal cual. Si quieres que actualice o regenere `requirements.txt`, indícamelo y lo actualizo.
- Para ejecutar pruebas:

  ```bash
  pytest
  ```

- Variables de entorno (ej. configuración): consulta `backend/config.py`.

---

Si deseas, puedo añadir un comando de PowerShell para ejecutar el servidor automáticamente o añadir más instrucciones para despliegues (Heroku, Docker, etc.).