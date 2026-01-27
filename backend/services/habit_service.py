"""
Servicio de lógica de negocio para hábitos.
Contiene todas las operaciones y validaciones.
"""

from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any
from backend.database.db import db
from backend.models.habit import Habit, Completion


class HabitService:
    """Servicio para manejar la lógica de negocio de hábitos"""
    
    @staticmethod
    def create_habit(data: Dict[str, Any]) -> Habit:
        """
        Crear un nuevo hábito con validaciones.
        
        Args:
            data: Diccionario con datos del hábito
            
        Returns:
            Habit: Objeto de hábito creado
            
        Raises:
            ValueError: Si los datos no son válidos
        """
        # Validaciones
        if not data.get('name'):
            raise ValueError("El nombre del hábito es requerido")
        
        if len(data['name']) > 100:
            raise ValueError("El nombre no puede exceder 100 caracteres")
        
        # Crear hábito
        habit = Habit(
            name=data['name'],
            description=data.get('description', ''),
            category=data.get('category', 'general'),
            frequency=data.get('frequency', 'daily')
        )
        
        db.session.add(habit)
        db.session.commit()
        
        return habit
    
    @staticmethod
    def get_all_habits(active_only: bool = True) -> List[Habit]:
        """
        Obtener todos los hábitos.
        
        Args:
            active_only: Si True, solo retorna hábitos activos
            
        Returns:
            List[Habit]: Lista de hábitos
        """
        query = Habit.query
        
        if active_only:
            query = query.filter_by(is_active=True)
        
        return query.order_by(Habit.created_at.desc()).all()
    
    @staticmethod
    def get_habit_by_id(habit_id: int) -> Optional[Habit]:
        """
        Obtener un hábito por su ID.
        
        Args:
            habit_id: ID del hábito
            
        Returns:
            Optional[Habit]: Hábito encontrado o None
        """
        return Habit.query.get(habit_id)
    
    @staticmethod
    def update_habit(habit_id: int, data: Dict[str, Any]) -> Optional[Habit]:
        """
        Actualizar un hábito existente.
        
        Args:
            habit_id: ID del hábito a actualizar
            data: Datos a actualizar
            
        Returns:
            Optional[Habit]: Hábito actualizado o None si no existe
        """
        habit = Habit.query.get(habit_id)
        
        if not habit:
            return None
        
        # Actualizar campos permitidos
        allowed_fields = ['name', 'description', 'category', 'frequency', 'is_active']
        for field in allowed_fields:
            if field in data:
                setattr(habit, field, data[field])
        
        habit.updated_at = datetime.utcnow()
        db.session.commit()
        
        return habit
    
    @staticmethod
    def delete_habit(habit_id: int) -> bool:
        """
        Eliminar un hábito (soft delete).
        
        Args:
            habit_id: ID del hábito a eliminar
            
        Returns:
            bool: True si se eliminó, False si no existe
        """
        habit = Habit.query.get(habit_id)
        
        if not habit:
            return False
        
        # Soft delete (marcar como inactivo)
        habit.is_active = False
        db.session.commit()
        
        return True
    
    @staticmethod
    def mark_completed(habit_id: int, notes: str = None) -> Optional[Completion]:
        """
        Marcar un hábito como completado hoy.
        
        Args:
            habit_id: ID del hábito
            notes: Notas opcionales
            
        Returns:
            Optional[Completion]: Objeto de completación o None
        """
        habit = Habit.query.get(habit_id)
        
        if not habit or not habit.is_active:
            return None
        
        # Verificar si ya fue completado hoy
        today = datetime.utcnow().date()
        already_completed = any(
            c.completed_date.date() == today
            for c in habit.completions
        )
        
        if already_completed:
            # Si ya está completado, quitar la completación
            Completion.query.filter(
                Completion.habit_id == habit_id,
                db.func.date(Completion.completed_date) == today
            ).delete()
            
            # Actualizar racha
            HabitService._update_streak(habit, completed=False)
        else:
            # Crear nueva completación
            completion = Completion(
                habit_id=habit_id,
                notes=notes
            )
            
            db.session.add(completion)
            
            # Actualizar racha
            HabitService._update_streak(habit, completed=True)
        
        db.session.commit()
        
        return completion if not already_completed else None
    
    @staticmethod
    def _update_streak(habit: Habit, completed: bool) -> None:
        """
        Actualizar la racha del hábito.
        
        Args:
            habit: Objeto hábito
            completed: Si se completó hoy
        """
        if not completed:
            # Si no se completó, reiniciar racha
            habit.current_streak = 0
            return
        
        # Obtener fecha de ayer
        yesterday = (datetime.utcnow() - timedelta(days=1)).date()
        
        # Verificar si se completó ayer
        completed_yesterday = any(
            c.completed_date.date() == yesterday
            for c in habit.completions
        )
        
        if completed_yesterday:
            # Continuar racha
            habit.current_streak += 1
        else:
            # Nueva racha
            habit.current_streak = 1
        
        # Actualizar mejor racha si es necesario
        if habit.current_streak > habit.best_streak:
            habit.best_streak = habit.current_streak
    
    @staticmethod
    def get_todays_habits() -> List[Dict[str, Any]]:
        """
        Obtener hábitos para hoy con estado de completación.
        
        Returns:
            List[Dict]: Lista de hábitos con info adicional
        """
        habits = Habit.query.filter_by(is_active=True).all()
        
        result = []
        for habit in habits:
            habit_dict = habit.to_dict()
            result.append(habit_dict)
        
        return result
    
    @staticmethod
    def get_habits_by_category() -> Dict[str, List[Habit]]:
        """
        Agrupar hábitos por categoría.
        
        Returns:
            Dict: Hábitos agrupados por categoría
        """
        habits = Habit.query.filter_by(is_active=True).all()
        categories = {}
        
        for habit in habits:
            if habit.category not in categories:
                categories[habit.category] = []
            categories[habit.category].append(habit)
        
        return categories
    
    @staticmethod
    def get_completion_stats(habit_id: int, days: int = 30) -> Dict[str, Any]:
        """
        Obtener estadísticas de completación para un hábito.
        
        Args:
            habit_id: ID del hábito
            days: Número de días a considerar
            
        Returns:
            Dict: Estadísticas
        """
        habit = Habit.query.get(habit_id)
        
        if not habit:
            return {}
        
        # Calcular fecha de inicio
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Contar completaciones en el período
        completions_count = Completion.query.filter(
            Completion.habit_id == habit_id,
            Completion.completed_date >= start_date
        ).count()
        
        # Calcular porcentaje
        completion_rate = (completions_count / days) * 100 if days > 0 else 0
        
        return {
            'habit_id': habit_id,
            'habit_name': habit.name,
            'period_days': days,
            'completions_count': completions_count,
            'completion_rate': round(completion_rate, 1),
            'current_streak': habit.current_streak,
            'best_streak': habit.best_streak
        }