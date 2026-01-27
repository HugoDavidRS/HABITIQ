"""
Rutas (endpoints) para la gestión de hábitos.
Controladores que manejan las peticiones HTTP.
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from backend.services.habit_service import HabitService

# Crear Blueprint para organizar rutas
habits_bp = Blueprint('habits', __name__)


@habits_bp.route('/')
def index():
    """Página principal - Dashboard"""
    habits = HabitService.get_todays_habits()
    categories = HabitService.get_habits_by_category()
    
    return render_template('dashboard.html', 
                         habits=habits, 
                         categories=categories,
                         today=datetime.utcnow().date())


@habits_bp.route('/habits')
def list_habits():
    """Listar todos los hábitos (página separada)"""
    habits = HabitService.get_all_habits()
    return render_template('index.html', habits=habits)


@habits_bp.route('/habits/new', methods=['GET', 'POST'])
def create_habit():
    """Crear nuevo hábito"""
    if request.method == 'POST':
        try:
            data = {
                'name': request.form.get('name'),
                'description': request.form.get('description'),
                'category': request.form.get('category'),
                'frequency': request.form.get('frequency', 'daily')
            }
            
            HabitService.create_habit(data)
            flash('¡Hábito creado exitosamente!', 'success')
            return redirect(url_for('habits.list_habits'))
        
        except ValueError as e:
            flash(str(e), 'error')
        except Exception as e:
            flash('Error al crear el hábito', 'error')
    
    # Categorías predefinidas
    categories = ['ejercicio', 'estudio', 'sueño', 'alimentación', 'productividad', 'general']
    
    return render_template('new_habit.html', categories=categories)


@habits_bp.route('/habits/<int:habit_id>/complete', methods=['POST'])
def toggle_complete(habit_id):
    """Marcar/desmarcar hábito como completado hoy"""
    try:
        notes = request.form.get('notes', '')
        HabitService.mark_completed(habit_id, notes)
        
        # Responder según el tipo de petición
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': True, 'habit_id': habit_id})
        
        flash('Estado actualizado correctamente', 'success')
    
    except Exception as e:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'error': str(e)}), 400
        flash('Error al actualizar el estado', 'error')
    
    return redirect(url_for('habits.index'))


@habits_bp.route('/habits/<int:habit_id>/edit', methods=['GET', 'POST'])
def edit_habit(habit_id):
    """Editar un hábito existente"""
    habit = HabitService.get_habit_by_id(habit_id)
    
    if not habit:
        flash('Hábito no encontrado', 'error')
        return redirect(url_for('habits.list_habits'))
    
    if request.method == 'POST':
        try:
            data = {
                'name': request.form.get('name'),
                'description': request.form.get('description'),
                'category': request.form.get('category'),
                'frequency': request.form.get('frequency'),
                'is_active': request.form.get('is_active') == 'true'
            }
            
            HabitService.update_habit(habit_id, data)
            flash('¡Hábito actualizado exitosamente!', 'success')
            return redirect(url_for('habits.list_habits'))
        
        except Exception as e:
            flash('Error al actualizar el hábito', 'error')
    
    categories = ['ejercicio', 'estudio', 'sueño', 'alimentación', 'productividad', 'general']
    
    return render_template('edit_habit.html', habit=habit, categories=categories)


@habits_bp.route('/habits/<int:habit_id>/delete', methods=['POST'])
def delete_habit(habit_id):
    """Eliminar un hábito (soft delete)"""
    try:
        success = HabitService.delete_habit(habit_id)
        
        if success:
            flash('Hábito eliminado correctamente', 'success')
        else:
            flash('Hábito no encontrado', 'error')
    
    except Exception as e:
        flash('Error al eliminar el hábito', 'error')
    
    return redirect(url_for('habits.list_habits'))


@habits_bp.route('/api/habits', methods=['GET'])
def api_list_habits():
    """API: Listar hábitos (JSON)"""
    habits = HabitService.get_all_habits()
    return jsonify([habit.to_dict() for habit in habits])


@habits_bp.route('/api/habits/<int:habit_id>/stats', methods=['GET'])
def api_habit_stats(habit_id):
    """API: Obtener estadísticas de un hábito"""
    days = request.args.get('days', 30, type=int)
    stats = HabitService.get_completion_stats(habit_id, days)
    
    if not stats:
        return jsonify({'error': 'Hábito no encontrado'}), 404
    
    return jsonify(stats)


# Importar aquí para evitar importación circular
from datetime import datetime