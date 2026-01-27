# Arquitectura del Sistema - HabitIQ

## Visión General
Aplicación web MVC con separación clara de responsabilidades.

## Capas

### 1. Capa de Presentación (Frontend)
- **Templates HTML:** Vistas renderizadas por Jinja2
- **CSS/JS:** Estilos y comportamiento del cliente
- Responsive design

### 2. Capa de Control (Backend - Routes)
- **Flask Blueprints:** Organización de endpoints
- **Controladores:** Manejo de requests/responses
- Validación básica de inputs

### 3. Capa de Servicios (Lógica de Negocio)
- **Servicios:** Reglas de negocio y operaciones complejas
- **Validaciones:** Reglas específicas del dominio
- **Métricas:** Cálculo de estadísticas

### 4. Capa de Datos
- **Modelos:** Entidades del sistema
- **Base de datos:** SQLite inicial → PostgreSQL
- **Repositorios:** Acceso a datos

## Flujo de Datos
Cliente → Routes → Services → Database → Services → Routes → Cliente