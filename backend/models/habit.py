"""
Modelo de datos para los hábitos.
Define la estructura de la tabla y métodos relacionados.
"""

from datetime import datetime, date
from backend.database.db import db


class Habit(db.Model):
    """
    Modelo que representa un hábito en el sistema.
    
    Attributes:
        id (int): Identificador único
        name (str): Nombre del hábito
        description (str): Descripción opcional
        category (str): Categoría (ejercicio, estudio, etc.)
        frequency (str): Frecuencia (diario, semanal)
        current_streak (int): Racha actual de cumplimiento
        best_streak (int): Mejor racha histórica
        created_at (datetime): Fecha de creación
        updated_at (datetime): Última actualización
        completions (relationship): Relación con las completaciones
    """
    
    __tablename__ = 'habits'
    
    # Columnas principales
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200))
    category = db.Column(db.String(50), nullable=False, default='general')
    frequency = db.Column(db.String(20), nullable=False, default='daily')
    current_streak = db.Column(db.Integer, default=0)
    best_streak = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relación con las completaciones
    completions = db.relationship('Completion', backref='habit', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Habit {self.id}: {self.name}>'
    
    def to_dict(self):
        """Convertir a diccionario para APIs o templates"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'frequency': self.frequency,
            'current_streak': self.current_streak,
            'best_streak': self.best_streak,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_active': self.is_active,
            'completed_today': self.completed_today()
        }
    
    def completed_today(self):
        """Verificar si el hábito fue completado hoy"""
        from backend.models.completion import Completion
        today = date.today()
        return any(
            completion.completed_date.date() == today
            for completion in self.completions
        )


class Completion(db.Model):
    """
    Modelo para registrar completaciones diarias de hábitos.
    """
    
    __tablename__ = 'completions'
    
    id = db.Column(db.Integer, primary_key=True)
    habit_id = db.Column(db.Integer, db.ForeignKey('habits.id'), nullable=False)
    completed_date = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.String(200))
    
    # Índice para búsquedas eficientes
    __table_args__ = (
        db.Index('idx_habit_date', 'habit_id', 'completed_date'),
    )
    
    def __repr__(self):
        return f'<Completion {self.id} for Habit {self.habit_id}>'