#!/usr/bin/env python3
"""
Script para inicializar la base de datos.
Crea las tablas y añade datos de ejemplo.
"""

import sys
import os

# Agregar backend al path
sys.path.append(os.path.join(os.path.dirname(__file__), '../backend'))

from app import create_app
from database.db import db
from models.habit import Habit, Completion
from datetime import datetime, timedelta


def init_database():
    """Inicializar base de datos con datos de ejemplo"""
    print("Inicializando base de datos HabitIQ...")
    
    # Crear aplicación
    app = create_app('development')
    
    with app.app_context():
        # Crear todas las tablas
        db.create_all()
        print("✅ Tablas creadas exitosamente")
        
        # Verificar si ya hay datos
        if Habit.query.first():
            print("⚠️  La base de datos ya contiene datos. Saltando inserción de ejemplos.")
            return
        
        # Crear hábitos de ejemplo
        sample_habits = [
            {
                'name': 'Ejercicio matutino',
                'description': '30 minutos de ejercicio cardiovascular',
                'category': 'ejercicio',
                'frequency': 'daily'
            },
            {
                'name': 'Leer antes de dormir',
                'description': 'Leer 20 páginas de un libro',
                'category': 'estudio',
                'frequency': 'daily'
            },
            {
                'name': 'Dormir 8 horas',
                'description': 'Mantener horario regular de sueño',
                'category': 'sueño',
                'frequency': 'daily'
            },
            {
                'name': 'Comer vegetales',
                'description': 'Incluir vegetales en cada comida principal',
                'category': 'alimentación',
                'frequency': 'daily'
            },
            {
                'name': 'Planificar el día',
                'description': 'Crear lista de tareas para el día siguiente',
                'category': 'productividad',
                'frequency': 'daily'
            },
            {
                'name': 'Meditación',
                'description': '10 minutos de meditación mindfulness',
                'category': 'general',
                'frequency': 'daily'
            },
            {
                'name': 'Revisión semanal',
                'description': 'Revisar objetivos y progreso de la semana',
                'category': 'productividad',
                'frequency': 'weekly'
            },
            {
                'name': 'Llamar a familia',
                'description': 'Contactar a un familiar o amigo cercano',
                'category': 'general',
                'frequency': 'weekly'
            }
        ]
        
        habits = []
        for habit_data in sample_habits:
            habit = Habit(**habit_data)
            db.session.add(habit)
            habits.append(habit)
        
        db.session.commit()
        print(f"✅ {len(habits)} hábitos de ejemplo creados")
        
        # Crear algunas completaciones de ejemplo (últimos 7 días)
        print("Generando historial de completaciones...")
        
        # Datos de completaciones por hábito (últimos 7 días)
        completion_patterns = {
            0: [0, 1, 2, 3, 4, 5, 6],  # Ejercicio: todos los días
            1: [0, 2, 4, 6],           # Leer: días alternos
            2: [0, 1, 2, 3, 4],        # Dormir: días de semana
            3: [1, 3, 5],              # Vegetales: días impares
            4: [0, 6],                 # Planificar: inicio y fin de semana
            5: [0, 1, 2, 3, 4, 5, 6],  # Meditación: todos los días
            6: [6],                    # Revisión semanal: domingos
            7: [3],                    # Llamar: miércoles
        }
        
        total_completions = 0
        today = datetime.utcnow()
        
        for habit_idx, days in completion_patterns.items():
            if habit_idx < len(habits):
                habit = habits[habit_idx]
                
                for day_offset in days:
                    # Calcular fecha (hace X días)
                    completion_date = today - timedelta(days=day_offset)
                    
                    # Crear completación
                    completion = Completion(
                        habit_id=habit.id,
                        completed_date=completion_date,
                        notes=f"Completado el {completion_date.strftime('%d/%m/%Y')}"
                    )
                    db.session.add(completion)
                    total_completions += 1
        
        db.session.commit()
        print(f"✅ {total_completions} completaciones de ejemplo creadas")
        
        # Calcular rachas basadas en las completaciones
        print("Calculando rachas...")
        for habit in habits:
            # Simular cálculo de rachas (simplificado para demo)
            completions = Completion.query.filter_by(habit_id=habit.id)\
                .order_by(Completion.completed_date.desc()).all()
            
            if completions:
                # Contar días consecutivos hasta hoy
                streak = 0
                current_date = today.date()
                
                for i in range(7):  # Últimos 7 días
                    check_date = current_date - timedelta(days=i)
                    has_completion = any(
                        c.completed_date.date() == check_date
                        for c in completions
                    )
                    
                    if has_completion:
                        streak += 1
                    else:
                        break
                
                habit.current_streak = streak
                habit.best_streak = max(habit.best_streak or 0, streak)
        
        db.session.commit()
        print("✅ Rachas calculadas")
        
        # Mostrar resumen
        print("\n" + "="*50)
        print("RESUMEN DE BASE DE DATOS")
        print("="*50)
        print(f"Total hábitos: {Habit.query.count()}")
        print(f"Total completaciones: {Completion.query.count()}")
        print(f"Hábitos activos: {Habit.query.filter_by(is_active=True).count()}")
        
        # Mostrar hábitos con sus rachas
        print("\nHábitos creados:")
        for habit in Habit.query.all():
            print(f"  • {habit.name}: {habit.current_streak} días de racha")
        
        print("\n✅ Base de datos inicializada exitosamente!")
        print("\nPara iniciar la aplicación:")
        print("1. python backend/app.py")
        print("2. Abrir http://localhost:5000 en tu navegador")


def clear_database():
    """Eliminar todos los datos de la base de datos"""
    print("⚠️  ADVERTENCIA: Esto eliminará todos los datos de la base de datos.")
    confirmation = input("¿Continuar? (s/n): ")
    
    if confirmation.lower() == 's':
        app = create_app('development')
        
        with app.app_context():
            # Eliminar todas las tablas
            db.drop_all()
            print("✅ Base de datos limpiada")
        
        # Volver a crear tablas
        init_database()


def show_help():
    """Mostrar ayuda"""
    print("""
Script de inicialización de base de datos - HabitIQ

Uso:
  python init_db.py [comando]

Comandos:
  init     - Inicializar base de datos (crear tablas y datos de ejemplo)
  clear    - Eliminar todos los datos y reinicializar
  help     - Mostrar este mensaje de ayuda

Si no se especifica comando, se ejecuta 'init' por defecto.
""")


if __name__ == '__main__':
    # Obtener comando (si existe)
    command = sys.argv[1] if len(sys.argv) > 1 else 'init'
    
    if command == 'init':
        init_database()
    elif command == 'clear':
        clear_database()
    elif command == 'help':
        show_help()
    else:
        print(f"Comando no reconocido: {command}")
        show_help()