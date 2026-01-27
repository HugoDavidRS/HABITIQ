# HabitIQ - Gestión Inteligente de Hábitos

Una aplicación web para gestión de hábitos diarios desarrollada con Python Flask.

## Características
- ✅ Registro de hábitos
- ✅ Seguimiento diario
- ✅ Dashboard de progreso
- ✅ Persistencia en base de datos

## Tecnologías
- **Backend:** Python 3.9+, Flask
- **Frontend:** HTML5, CSS3, JavaScript
- **Base de datos:** SQLite (con migración a PostgreSQL)
- **Arquitectura:** MVC / Clean Architecture

## Instalación
1. Clonar repositorio
2. `pip install -r requirements.txt`
3. `python scripts/init_db.py`
4. `python backend/app.py`

## Estructura del Proyecto

HabitIQ/
├── README.md
├── requirements.txt
├── .gitignore
│
├── docs/
│   ├── arquitectura.md
│   ├── alcance.md
│   └── definicion_proyecto.md
│
├── backend/
│   ├── app.py
│   ├── config.py
│   │
│   ├── models/
│   │   └── habit.py
│   │
│   ├── routes/
│   │   └── habits.py
│   │
│   ├── services/
│   │   └── habit_service.py
│   │
│   └── database/
│       ├── db.py
│       └── habits.db
│
├── frontend/
│   ├── templates/
│   │   ├── base.html
│   │   ├── index.html
│   │   ├── dashboard.html
│   │   ├── new_habit.html
│   │   ├── edit_habit.html
│   │   ├── 404.html
│   │   └── 500.html
│   │
│   └── static/
│       ├── css/
│       │   └── style.css
│       ├── js/
│       │   └── main.js
│       └── img/
│           └── favicon.ico
│
├── tests/
│   └── test_habits.py
│
└── scripts/
    └── init_db.py