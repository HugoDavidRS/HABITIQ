"""
Tests unitarios para el módulo de hábitos.
"""

import unittest
import tempfile
import os
import sys
from datetime import datetime, timedelta

# Agregar backend al path
sys.path.append(os.path.join(os.path.dirname(__file__), '../backend'))

from app import create_app
from database.db import db
from models.habit import Habit, Completion
from services.habit_service import HabitService


class TestConfig:
    """Configuración para testing"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 'test-secret-key'


class HabitModelTestCase(unittest.TestCase):
    """Tests para el modelo Habit"""
    
    def setUp(self):
        """Configurar test antes de cada método"""
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        db.create_all()
        
        # Datos de prueba
        self.habit_data = {
            'name': 'Test Habit',
            'description': 'Test Description',
            'category': 'exercise',
            'frequency': 'daily'
        }
    
    def tearDown(self):
        """Limpiar después de cada test"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def test_create_habit(self):
        """Test: Crear un nuevo hábito"""
        habit = Habit(**self.habit_data)
        db.session.add(habit)
        db.session.commit()
        
        self.assertIsNotNone(habit.id)
        self.assertEqual(habit.name, 'Test Habit')
        self.assertEqual(habit.category, 'exercise')
        self.assertTrue(habit.is_active)
        self.assertEqual(habit.current_streak, 0)
        self.assertEqual(habit.best_streak, 0)
    
    def test_habit_to_dict(self):
        """Test: Convertir hábito a diccionario"""
        habit = Habit(**self.habit_data)
        db.session.add(habit)
        db.session.commit()
        
        habit_dict = habit.to_dict()
        
        self.assertEqual(habit_dict['name'], 'Test Habit')
        self.assertEqual(habit_dict['category'], 'exercise')
        self.assertEqual(habit_dict['current_streak'], 0)
        self.assertTrue('created_at' in habit_dict)
    
    def test_habit_completed_today(self):
        """Test: Verificar si hábito fue completado hoy"""
        habit = Habit(**self.habit_data)
        db.session.add(habit)
        db.session.commit()
        
        # No debería estar completado
        self.assertFalse(habit.completed_today())
        
        # Completar hoy
        completion = Completion(habit_id=habit.id)
        db.session.add(completion)
        db.session.commit()
        
        # Ahora debería estar completado
        self.assertTrue(habit.completed_today())
    
    def test_habit_repr(self):
        """Test: Representación string del hábito"""
        habit = Habit(**self.habit_data)
        self.assertIn('Test Habit', str(habit))


class HabitServiceTestCase(unittest.TestCase):
    """Tests para el servicio de hábitos"""
    
    def setUp(self):
        """Configurar test antes de cada método"""
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        db.create_all()
        
        # Datos de prueba
        self.habit_data = {
            'name': 'Test Habit',
            'description': 'Test Description',
            'category': 'exercise',
            'frequency': 'daily'
        }
    
    def tearDown(self):
        """Limpiar después de cada test"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def test_create_habit_service(self):
        """Test: Crear hábito usando servicio"""
        habit = HabitService.create_habit(self.habit_data)
        
        self.assertIsNotNone(habit.id)
        self.assertEqual(habit.name, 'Test Habit')
        self.assertEqual(habit.category, 'exercise')
    
    def test_create_habit_validation(self):
        """Test: Validación al crear hábito"""
        # Test sin nombre
        with self.assertRaises(ValueError):
            HabitService.create_habit({'category': 'exercise'})
        
        # Test con nombre muy largo
        with self.assertRaises(ValueError):
            HabitService.create_habit({
                'name': 'A' * 101,  # 101 caracteres
                'category': 'exercise'
            })
    
    def test_get_all_habits(self):
        """Test: Obtener todos los hábitos"""
        # Crear varios hábitos
        habit1 = HabitService.create_habit(self.habit_data)
        habit2 = HabitService.create_habit({
            'name': 'Test Habit 2',
            'category': 'study'
        })
        
        habits = HabitService.get_all_habits()
        
        self.assertEqual(len(habits), 2)
        self.assertEqual(habits[0].name, 'Test Habit 2')  # Ordenado por fecha descendente
    
    def test_get_habit_by_id(self):
        """Test: Obtener hábito por ID"""
        habit = HabitService.create_habit(self.habit_data)
        
        found_habit = HabitService.get_habit_by_id(habit.id)
        
        self.assertIsNotNone(found_habit)
        self.assertEqual(found_habit.name, 'Test Habit')
        
        # Test con ID inexistente
        nonexistent = HabitService.get_habit_by_id(999)
        self.assertIsNone(nonexistent)
    
    def test_update_habit(self):
        """Test: Actualizar hábito"""
        habit = HabitService.create_habit(self.habit_data)
        
        updated = HabitService.update_habit(habit.id, {
            'name': 'Updated Habit',
            'description': 'Updated Description',
            'is_active': False
        })
        
        self.assertEqual(updated.name, 'Updated Habit')
        self.assertEqual(updated.description, 'Updated Description')
        self.assertFalse(updated.is_active)
    
    def test_delete_habit(self):
        """Test: Eliminar hábito (soft delete)"""
        habit = HabitService.create_habit(self.habit_data)
        
        # Soft delete
        success = HabitService.delete_habit(habit.id)
        self.assertTrue(success)
        
        # Verificar que está marcado como inactivo
        deleted_habit = HabitService.get_habit_by_id(habit.id)
        self.assertFalse(deleted_habit.is_active)
        
        # Test eliminar hábito inexistente
        success = HabitService.delete_habit(999)
        self.assertFalse(success)
    
    def test_mark_completed(self):
        """Test: Marcar hábito como completado"""
        habit = HabitService.create_habit(self.habit_data)
        
        # Marcar como completado
        completion = HabitService.mark_completed(habit.id, 'Test notes')
        self.assertIsNotNone(completion)
        
        # Verificar que se creó la completación
        habit = HabitService.get_habit_by_id(habit.id)
        self.assertTrue(habit.completed_today())
        self.assertEqual(habit.current_streak, 1)
        
        # Desmarcar completación
        HabitService.mark_completed(habit.id)
        habit = HabitService.get_habit_by_id(habit.id)
        self.assertFalse(habit.completed_today())
        self.assertEqual(habit.current_streak, 0)
    
    def test_get_todays_habits(self):
        """Test: Obtener hábitos para hoy"""
        # Crear hábitos
        habit1 = HabitService.create_habit(self.habit_data)
        habit2 = HabitService.create_habit({
            'name': 'Test Habit 2',
            'category': 'study'
        })
        
        # Marcar uno como completado
        HabitService.mark_completed(habit1.id)
        
        habits = HabitService.get_todays_habits()
        
        self.assertEqual(len(habits), 2)
        # Verificar que el primer hábito está marcado como completado hoy
        self.assertTrue(habits[0]['completed_today'])
    
    def test_get_completion_stats(self):
        """Test: Obtener estadísticas de completación"""
        habit = HabitService.create_habit(self.habit_data)
        
        # Completar varios días
        for i in range(5):
            HabitService.mark_completed(habit.id)
        
        stats = HabitService.get_completion_stats(habit.id, days=30)
        
        self.assertEqual(stats['habit_id'], habit.id)
        self.assertEqual(stats['habit_name'], 'Test Habit')
        self.assertEqual(stats['current_streak'], 5)
        self.assertEqual(stats['completions_count'], 5)
        
        # Calcular tasa esperada (5/30 = 16.7%)
        expected_rate = round((5 / 30) * 100, 1)
        self.assertEqual(stats['completion_rate'], expected_rate)
    
    def test_get_habits_by_category(self):
        """Test: Agrupar hábitos por categoría"""
        # Crear hábitos en diferentes categorías
        HabitService.create_habit({'name': 'Exercise', 'category': 'exercise'})
        HabitService.create_habit({'name': 'Study', 'category': 'study'})
        HabitService.create_habit({'name': 'Exercise 2', 'category': 'exercise'})
        
        categories = HabitService.get_habits_by_category()
        
        self.assertIn('exercise', categories)
        self.assertIn('study', categories)
        self.assertEqual(len(categories['exercise']), 2)
        self.assertEqual(len(categories['study']), 1)


class CompletionModelTestCase(unittest.TestCase):
    """Tests para el modelo Completion"""
    
    def setUp(self):
        """Configurar test antes de cada método"""
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        db.create_all()
        
        # Crear hábito de prueba
        self.habit = Habit(
            name='Test Habit',
            category='exercise',
            frequency='daily'
        )
        db.session.add(self.habit)
        db.session.commit()
    
    def tearDown(self):
        """Limpiar después de cada test"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def test_create_completion(self):
        """Test: Crear una completación"""
        completion = Completion(
            habit_id=self.habit.id,
            notes='Test notes'
        )
        db.session.add(completion)
        db.session.commit()
        
        self.assertIsNotNone(completion.id)
        self.assertEqual(completion.habit_id, self.habit.id)
        self.assertEqual(completion.notes, 'Test notes')
        self.assertIsNotNone(completion.completed_date)
    
    def test_completion_repr(self):
        """Test: Representación string de la completación"""
        completion = Completion(habit_id=self.habit.id)
        self.assertIn(str(self.habit.id), str(completion))


if __name__ == '__main__':
    unittest.main()