"""
Versión simplificada de app.py para solucionar problemas de importación
"""

import os
import sys
from datetime import datetime, date

# Agregar directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify

# Crear aplicación Flask directamente
app = Flask(__name__,
            static_folder='../frontend/static',
            template_folder='../frontend/templates')

# Configuración básica
app.config['SECRET_KEY'] = 'dev-key-habitiq-12345'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///../backend/database/habits.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializar SQLAlchemy
from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy(app)

# Definir modelos
class Habit(db.Model):
    __tablename__ = 'habits'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200))
    category = db.Column(db.String(50), nullable=False, default='general')
    frequency = db.Column(db.String(20), nullable=False, default='daily')
    current_streak = db.Column(db.Integer, default=0)
    best_streak = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.utcnow())

class Completion(db.Model):
    __tablename__ = 'completions'
    id = db.Column(db.Integer, primary_key=True)
    habit_id = db.Column(db.Integer, db.ForeignKey('habits.id'), nullable=False)
    completed_date = db.Column(db.DateTime, default=lambda: datetime.utcnow())
    notes = db.Column(db.String(200))

# FUNCIÓN HELPER para verificar si un hábito fue completado hoy
def is_completed_today(habit_id):
    """Verificar si un hábito fue completado hoy"""
    today = datetime.utcnow().date()
    completion = Completion.query.filter(
        Completion.habit_id == habit_id,
        db.func.date(Completion.completed_date) == today
    ).first()
    return completion is not None

# Hacerla disponible en los templates
app.jinja_env.globals.update(is_completed_today=is_completed_today)

# Rutas básicas
@app.route('/')
def index():
    """Página principal / lista de hábitos"""
    # Obtener hábitos de la base de datos
    habits_list = Habit.query.order_by(Habit.created_at.desc()).all()
    return render_template('index.html', habits=habits_list)

@app.route('/habits')
def list_habits():
    """Alias para la lista de hábitos"""
    return redirect(url_for('index'))

@app.route('/habits/new', methods=['GET', 'POST'])
def create_habit():
    """Crear nuevo hábito"""
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            description = request.form.get('description', '')
            category = request.form.get('category', 'general')
            frequency = request.form.get('frequency', 'daily')
            
            if not name:
                flash('El nombre del hábito es requerido', 'error')
                return redirect(url_for('create_habit'))
            
            new_habit = Habit(
                name=name,
                description=description,
                category=category,
                frequency=frequency
            )
            
            db.session.add(new_habit)
            db.session.commit()
            
            flash(f'¡Hábito "{name}" creado exitosamente!', 'success')
            return redirect(url_for('index'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear el hábito: {str(e)}', 'error')
            return redirect(url_for('create_habit'))
    
    # Lista de categorías para el select
    categories = ['health', 'fitness', 'learning', 'productivity', 'mindfulness', 'finance', 'social', 'general']
    
    return render_template('new_habit.html', categories=categories)

@app.route('/habits/toggle/<int:habit_id>', methods=['POST'])
def toggle_complete(habit_id):
    """Marcar/desmarcar hábito como completado hoy (soporta AJAX)"""
    habit = Habit.query.get_or_404(habit_id)
    
    # Verificar si ya se completó hoy
    today = datetime.utcnow().date()
    existing_completion = Completion.query.filter(
        Completion.habit_id == habit_id,
        db.func.date(Completion.completed_date) == today
    ).first()
    
    if existing_completion:
        # Si ya está completado, eliminar la completación
        db.session.delete(existing_completion)
        habit.current_streak = max(0, habit.current_streak - 1)
        db.session.commit()
        message = f'Completación de "{habit.name}" removida'
        completed = False
        flash_message_type = 'info'
    else:
        # Si no está completado, crear nueva completación
        new_completion = Completion(habit_id=habit_id)
        db.session.add(new_completion)
        
        # Actualizar racha
        habit.current_streak += 1
        if habit.current_streak > habit.best_streak:
            habit.best_streak = habit.current_streak
        
        db.session.commit()
        message = f'¡Hábito "{habit.name}" completado! 🎉'
        completed = True
        flash_message_type = 'success'
    
    # Si es una petición AJAX, devolver JSON
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    if is_ajax:
        return jsonify({
            'success': True,
            'message': message,
            'completed': completed,
            'habit_id': habit_id,
            'habit_name': habit.name,
            'current_streak': habit.current_streak,
            'best_streak': habit.best_streak
        })
    
    # Si no es AJAX, comportamiento normal
    flash(message, flash_message_type)
    return redirect(request.referrer or url_for('index'))

@app.route('/habits/edit/<int:habit_id>', methods=['GET', 'POST'])
def edit_habit(habit_id):
    """Editar un hábito existente"""
    habit = Habit.query.get_or_404(habit_id)
    
    if request.method == 'POST':
        try:
            habit.name = request.form.get('name', habit.name)
            habit.description = request.form.get('description', habit.description)
            habit.category = request.form.get('category', habit.category)
            habit.frequency = request.form.get('frequency', habit.frequency)
            
            db.session.commit()
            flash(f'Hábito "{habit.name}" actualizado exitosamente', 'success')
            return redirect(url_for('index'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar el hábito: {str(e)}', 'error')
    
    # Lista de categorías para el select
    categories = ['health', 'fitness', 'learning', 'productivity', 'mindfulness', 'finance', 'social', 'general']
    
    return render_template('edit_habit.html', habit=habit, categories=categories)

@app.route('/habits/<int:habit_id>/delete', methods=['POST'])
def delete_habit(habit_id):
    """Eliminar hábito"""
    habit = Habit.query.get_or_404(habit_id)
    habit_name = habit.name
    
    # Eliminar completaciones primero
    Completion.query.filter_by(habit_id=habit_id).delete()
    
    # Eliminar hábito
    db.session.delete(habit)
    db.session.commit()
    
    flash(f'Hábito "{habit_name}" eliminado exitosamente', 'success')
    return redirect(url_for('index'))

@app.route('/habits/<int:habit_id>/toggle', methods=['POST'])
def toggle_habit(habit_id):
    """Activar/desactivar hábito"""
    habit = Habit.query.get_or_404(habit_id)
    habit.is_active = not habit.is_active
    db.session.commit()
    
    status = "activado" if habit.is_active else "desactivado"
    flash(f'Hábito "{habit.name}" {status}', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    """Dashboard con estadísticas"""
    from datetime import datetime, date
    
    # Obtener fecha actual
    today = datetime.now()
    
    # Obtener hábitos
    habits = Habit.query.all()
    
    # Calcular hábitos completados hoy
    completed_today = Completion.query.filter(
        db.func.date(Completion.completed_date) == date.today()
    ).count()
    
    # Obtener categorías agrupadas
    categories = {}
    for habit in habits:
        if habit.category not in categories:
            categories[habit.category] = []
        categories[habit.category].append(habit)
    
    # Calcular estadísticas
    total_habits = len(habits)
    active_habits = sum(1 for habit in habits if habit.is_active)
    
    # Hábitos con mejor racha
    best_streak_habit = Habit.query.order_by(Habit.best_streak.desc()).first()
    
    # Determinar qué hábitos fueron completados hoy
    habit_ids_completed_today = [
        completion.habit_id 
        for completion in Completion.query.filter(
            db.func.date(Completion.completed_date) == date.today()
        ).all()
    ]
    
    for habit in habits:
        habit.completed_today = habit.id in habit_ids_completed_today
    
    return render_template('dashboard.html',
                         today=today,
                         habits=habits,
                         categories=categories,
                         total_habits=total_habits,
                         active_habits=active_habits,
                         completed_today=completed_today,
                         best_streak_habit=best_streak_habit)

@app.route('/api/habits')
def api_habits():
    """API para obtener hábitos (para AJAX)"""
    habits = Habit.query.all()
    result = []
    for habit in habits:
        result.append({
            'id': habit.id,
            'name': habit.name,
            'category': habit.category,
            'frequency': habit.frequency,
            'current_streak': habit.current_streak,
            'best_streak': habit.best_streak,
            'is_active': habit.is_active,
            'completed_today': is_completed_today(habit.id)
        })
    return jsonify(result)

@app.route('/api/dashboard/stats')
def api_dashboard_stats():
    """API para obtener estadísticas del dashboard (AJAX)"""
    from datetime import date
    
    total_habits = Habit.query.count()
    active_habits = Habit.query.filter_by(is_active=True).count()
    completed_today = Completion.query.filter(
        db.func.date(Completion.completed_date) == date.today()
    ).count()
    
    best_streak_habit = Habit.query.order_by(Habit.best_streak.desc()).first()
    
    return jsonify({
        'total_habits': total_habits,
        'active_habits': active_habits,
        'completed_today': completed_today,
        'best_streak': best_streak_habit.best_streak if best_streak_habit else 0,
        'best_streak_habit': best_streak_habit.name if best_streak_habit else 'Ninguno'
    })

@app.route('/health')
def health():
    return {'status': 'ok', 'message': 'HabitIQ funcionando'}

# Función para crear tablas
def create_tables():
    with app.app_context():
        db.create_all()
        print("✅ Tablas creadas")

if __name__ == '__main__':
    # Crear tablas si no existen
    create_tables()
    
    print("=" * 50)
    print("🚀 HABITIQ - Servidor iniciando")
    print("=" * 50)
    print("📁 Base de datos: backend/database/habits.db")
    print("🌐 URL: http://localhost:5000")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=5000, debug=True)