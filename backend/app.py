"""
HabitIQ - Gestión Inteligente de Hábitos
App principal con autenticación de usuarios
"""

import os
import sys
from datetime import datetime, date

# Agregar directorio raíz al path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from dotenv import load_dotenv
load_dotenv(os.path.join(BASE_DIR, '.env'))

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from backend.database.db import db, init_app
import sqlalchemy

# Crear aplicación Flask
app = Flask(__name__,
            static_folder='../frontend/static',
            template_folder='../frontend/templates')

# Configuración
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-habitiq-12345')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///../backend/database/habits.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_recycle': 280, 'pool_pre_ping': True}

# Probar conexión a la base de datos indicada en .env. Si falla, usar
# fallback a SQLite local para que la app pueda arrancar y el usuario pueda
# seguir trabajando localmente.
db_url = app.config['SQLALCHEMY_DATABASE_URI']
try:
    # Intento rápido de conexión (timeout corto)
    engine = sqlalchemy.create_engine(db_url, connect_args={"connect_timeout": 5})
    conn = engine.connect()
    conn.close()
    print(f"✅ Conexión a la base de datos OK: {db_url}")
except Exception as e:
    print("⚠️ No se pudo conectar a la BD remota:", str(e))
    # Fallback a SQLite local
    fallback = 'sqlite:///../backend/database/habits.db'
    app.config['SQLALCHEMY_DATABASE_URI'] = fallback
    print(f"Usando base de datos local de fallback: {app.config['SQLALCHEMY_DATABASE_URI']}")

# Inicializar extensiones
init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Inicia sesión para acceder a esta página'
login_manager.login_message_category = 'info'

# ========== MODELOS ==========

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    bio = db.Column(db.String(300), default='')
    avatar_color = db.Column(db.String(7), default='#6366f1')
    is_public = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.utcnow())
    habits = db.relationship('Habit', backref='user', lazy=True, cascade='all, delete-orphan')
    achievements = db.relationship('UserAchievement', backref='user', lazy=True, cascade='all, delete-orphan')

    # Friendships where this user sent the request
    sent_requests = db.relationship('Friendship', foreign_keys='Friendship.user_id', backref='sender', lazy=True)
    received_requests = db.relationship('Friendship', foreign_keys='Friendship.friend_id', backref='receiver', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_friends(self):
        """Get all accepted friends"""
        sent = Friendship.query.filter_by(user_id=self.id, status='accepted').all()
        received = Friendship.query.filter_by(friend_id=self.id, status='accepted').all()
        friends = [f.receiver for f in sent] + [f.sender for f in received]
        return friends

    def get_pending_received(self):
        """Get pending friend requests received"""
        return Friendship.query.filter_by(friend_id=self.id, status='pending').all()

    def friendship_with(self, other_id):
        """Check friendship status with another user"""
        f = Friendship.query.filter(
            db.or_(
                db.and_(Friendship.user_id == self.id, Friendship.friend_id == other_id),
                db.and_(Friendship.user_id == other_id, Friendship.friend_id == self.id)
            )
        ).first()
        return f


class Friendship(db.Model):
    __tablename__ = 'friendships'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    friend_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, accepted, rejected
    created_at = db.Column(db.DateTime, default=lambda: datetime.utcnow())


class Achievement(db.Model):
    __tablename__ = 'achievements'
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200))
    icon = db.Column(db.String(50), default='fa-trophy')
    color = db.Column(db.String(7), default='#f59e0b')
    category = db.Column(db.String(50), default='general')  # streak, completion, social, milestone


class UserAchievement(db.Model):
    __tablename__ = 'user_achievements'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    achievement_id = db.Column(db.Integer, db.ForeignKey('achievements.id'), nullable=False)
    earned_at = db.Column(db.DateTime, default=lambda: datetime.utcnow())
    achievement = db.relationship('Achievement', backref='user_achievements')


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class Habit(db.Model):
    __tablename__ = 'habits'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200))
    category = db.Column(db.String(50), nullable=False, default='general')
    frequency = db.Column(db.String(20), nullable=False, default='daily')
    current_streak = db.Column(db.Integer, default=0)
    best_streak = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.utcnow())
    completions = db.relationship('Completion', backref='habit', lazy=True, cascade='all, delete-orphan')

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

# ========== RUTAS PÚBLICAS ==========

@app.route('/')
def landing():
    """Landing page pública"""
    if current_user.is_authenticated:
        return redirect(url_for('habits_app'))
    return render_template('landing.html')

@app.route('/pricing')
def pricing():
    """Página de planes y precios"""
    return render_template('pricing.html')

# ========== RUTAS DE AUTENTICACIÓN ==========

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Registro de nuevo usuario"""
    if current_user.is_authenticated:
        return redirect(url_for('habits_app'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # Validaciones
        if not username or not email or not password:
            flash('Todos los campos son requeridos', 'error')
            return render_template('register.html')
        
        if len(username) < 3:
            flash('El nombre de usuario debe tener al menos 3 caracteres', 'error')
            return render_template('register.html')
        
        if len(password) < 6:
            flash('La contraseña debe tener al menos 6 caracteres', 'error')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Las contraseñas no coinciden', 'error')
            return render_template('register.html')
        
        if User.query.filter_by(username=username).first():
            flash('Este nombre de usuario ya está en uso', 'error')
            return render_template('register.html')
        
        if User.query.filter_by(email=email).first():
            flash('Este email ya está registrado', 'error')
            return render_template('register.html')
        
        # Crear usuario
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        login_user(user)
        flash(f'¡Bienvenido a HabitIQ, {username}!', 'success')
        return redirect(url_for('habits_app'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Inicio de sesión"""
    if current_user.is_authenticated:
        return redirect(url_for('habits_app'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False)
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user, remember=bool(remember))
            next_page = request.args.get('next')
            flash(f'¡Hola de nuevo, {user.username}!', 'success')
            return redirect(next_page or url_for('habits_app'))
        else:
            flash('Email o contraseña incorrectos', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """Cerrar sesión"""
    logout_user()
    flash('Sesión cerrada correctamente', 'info')
    return redirect(url_for('landing'))

# ========== RUTAS DE HÁBITOS ==========

@app.route('/app')
@login_required
def habits_app():
    """Página principal de hábitos (requiere login)"""
    habits_list = Habit.query.filter_by(user_id=current_user.id).order_by(Habit.created_at.desc()).all()
    return render_template('index.html', habits=habits_list)

@app.route('/habits')
@login_required
def list_habits():
    """Alias para la lista de hábitos"""
    return redirect(url_for('habits_app'))

@app.route('/habits/new', methods=['GET', 'POST'])
@login_required
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
                user_id=current_user.id,
                name=name,
                description=description,
                category=category,
                frequency=frequency
            )
            
            db.session.add(new_habit)
            db.session.commit()
            
            flash(f'¡Hábito "{name}" creado exitosamente!', 'success')
            return redirect(url_for('habits_app'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear el hábito: {str(e)}', 'error')
            return redirect(url_for('create_habit'))
    
    # Lista de categorías para el select
    categories = ['health', 'fitness', 'learning', 'productivity', 'mindfulness', 'finance', 'social', 'general']
    
    return render_template('new_habit.html', categories=categories)

@app.route('/habits/toggle/<int:habit_id>', methods=['POST'])
@login_required
def toggle_complete(habit_id):
    """Marcar/desmarcar hábito como completado hoy (soporta AJAX)"""
    habit = Habit.query.filter_by(id=habit_id, user_id=current_user.id).first_or_404()
    
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
    return redirect(request.referrer or url_for('habits_app'))

@app.route('/habits/edit/<int:habit_id>', methods=['GET', 'POST'])
@login_required
def edit_habit(habit_id):
    """Editar un hábito existente"""
    habit = Habit.query.filter_by(id=habit_id, user_id=current_user.id).first_or_404()
    
    if request.method == 'POST':
        try:
            habit.name = request.form.get('name', habit.name)
            habit.description = request.form.get('description', habit.description)
            habit.category = request.form.get('category', habit.category)
            habit.frequency = request.form.get('frequency', habit.frequency)
            
            db.session.commit()
            flash(f'Hábito "{habit.name}" actualizado exitosamente', 'success')
            return redirect(url_for('habits_app'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar el hábito: {str(e)}', 'error')
    
    # Lista de categorías para el select
    categories = ['health', 'fitness', 'learning', 'productivity', 'mindfulness', 'finance', 'social', 'general']
    
    return render_template('edit_habit.html', habit=habit, categories=categories)

@app.route('/habits/<int:habit_id>/delete', methods=['POST'])
@login_required
def delete_habit(habit_id):
    """Eliminar hábito"""
    habit = Habit.query.filter_by(id=habit_id, user_id=current_user.id).first_or_404()
    habit_name = habit.name
    
    # Eliminar completaciones primero
    Completion.query.filter_by(habit_id=habit_id).delete()
    
    # Eliminar hábito
    db.session.delete(habit)
    db.session.commit()
    
    flash(f'Hábito "{habit_name}" eliminado exitosamente', 'success')
    return redirect(url_for('habits_app'))

@app.route('/habits/<int:habit_id>/toggle', methods=['POST'])
@login_required
def toggle_habit(habit_id):
    """Activar/desactivar hábito"""
    habit = Habit.query.filter_by(id=habit_id, user_id=current_user.id).first_or_404()
    habit.is_active = not habit.is_active
    db.session.commit()
    
    status = "activado" if habit.is_active else "desactivado"
    flash(f'Hábito "{habit.name}" {status}', 'info')
    return redirect(url_for('habits_app'))

@app.route('/dashboard')
@login_required
def dashboard():
    """Dashboard con estadísticas"""
    from datetime import datetime, date
    
    # Obtener fecha actual
    today = datetime.now()
    
    # Obtener hábitos del usuario actual
    habits = Habit.query.filter_by(user_id=current_user.id).all()
    
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
    best_streak_habit = Habit.query.filter_by(user_id=current_user.id).order_by(Habit.best_streak.desc()).first()
    
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
@login_required
def api_habits():
    """API para obtener hábitos (para AJAX)"""
    habits = Habit.query.filter_by(user_id=current_user.id).all()
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
@login_required
def api_dashboard_stats():
    """API para obtener estadísticas del dashboard (AJAX)"""
    from datetime import date
    
    total_habits = Habit.query.filter_by(user_id=current_user.id).count()
    active_habits = Habit.query.filter_by(user_id=current_user.id, is_active=True).count()
    completed_today = Completion.query.filter(
        db.func.date(Completion.completed_date) == date.today()
    ).count()
    
    best_streak_habit = Habit.query.filter_by(user_id=current_user.id).order_by(Habit.best_streak.desc()).first()
    
    return jsonify({
        'total_habits': total_habits,
        'active_habits': active_habits,
        'completed_today': completed_today,
        'best_streak': best_streak_habit.best_streak if best_streak_habit else 0,
        'best_streak_habit': best_streak_habit.name if best_streak_habit else 'Ninguno'
    })

# ========== LOGROS / ACHIEVEMENTS ==========

ACHIEVEMENT_DEFINITIONS = [
    {'key': 'first_habit', 'name': 'Primer Paso', 'description': 'Crea tu primer habito', 'icon': 'fa-seedling', 'color': '#10b981', 'category': 'milestone'},
    {'key': 'five_habits', 'name': 'Coleccionista', 'description': 'Crea 5 habitos', 'icon': 'fa-layer-group', 'color': '#6366f1', 'category': 'milestone'},
    {'key': 'ten_habits', 'name': 'Dedicado', 'description': 'Crea 10 habitos', 'icon': 'fa-cubes', 'color': '#8b5cf6', 'category': 'milestone'},
    {'key': 'streak_3', 'name': 'En Racha', 'description': 'Alcanza una racha de 3 dias', 'icon': 'fa-fire', 'color': '#f59e0b', 'category': 'streak'},
    {'key': 'streak_7', 'name': 'Semana Perfecta', 'description': 'Alcanza una racha de 7 dias', 'icon': 'fa-fire-flame-curved', 'color': '#ef4444', 'category': 'streak'},
    {'key': 'streak_30', 'name': 'Imparable', 'description': 'Alcanza una racha de 30 dias', 'icon': 'fa-meteor', 'color': '#f43f5e', 'category': 'streak'},
    {'key': 'streak_100', 'name': 'Leyenda', 'description': 'Alcanza una racha de 100 dias', 'icon': 'fa-crown', 'color': '#eab308', 'category': 'streak'},
    {'key': 'first_complete', 'name': 'Check!', 'description': 'Completa un habito por primera vez', 'icon': 'fa-check', 'color': '#10b981', 'category': 'completion'},
    {'key': 'fifty_completions', 'name': 'Constante', 'description': 'Acumula 50 completaciones', 'icon': 'fa-star', 'color': '#6366f1', 'category': 'completion'},
    {'key': 'hundred_completions', 'name': 'Centurion', 'description': 'Acumula 100 completaciones', 'icon': 'fa-medal', 'color': '#f59e0b', 'category': 'completion'},
    {'key': 'first_friend', 'name': 'Social', 'description': 'Agrega tu primer amigo', 'icon': 'fa-user-plus', 'color': '#06b6d4', 'category': 'social'},
    {'key': 'five_friends', 'name': 'Popular', 'description': 'Ten 5 amigos', 'icon': 'fa-users', 'color': '#8b5cf6', 'category': 'social'},
    {'key': 'perfect_day', 'name': 'Dia Perfecto', 'description': 'Completa todos tus habitos en un dia', 'icon': 'fa-sun', 'color': '#f59e0b', 'category': 'completion'},
]

def seed_achievements():
    """Seed achievement definitions into DB"""
    for ach_def in ACHIEVEMENT_DEFINITIONS:
        existing = Achievement.query.filter_by(key=ach_def['key']).first()
        if not existing:
            ach = Achievement(**ach_def)
            db.session.add(ach)
    db.session.commit()

def check_achievements(user):
    """Check and award achievements for a user"""
    earned_keys = {ua.achievement.key for ua in user.achievements}
    new_achievements = []

    habit_count = Habit.query.filter_by(user_id=user.id).count()
    total_completions = Completion.query.join(Habit).filter(Habit.user_id == user.id).count()
    best_streak = db.session.query(db.func.max(Habit.best_streak)).filter(Habit.user_id == user.id).scalar() or 0
    friend_count = len(user.get_friends())

    # Check today perfect day
    today_total = Habit.query.filter_by(user_id=user.id, is_active=True).count()
    today_done = Completion.query.join(Habit).filter(
        Habit.user_id == user.id,
        db.func.date(Completion.completed_date) == date.today()
    ).count()
    perfect_day = today_total > 0 and today_done >= today_total

    checks = {
        'first_habit': habit_count >= 1,
        'five_habits': habit_count >= 5,
        'ten_habits': habit_count >= 10,
        'streak_3': best_streak >= 3,
        'streak_7': best_streak >= 7,
        'streak_30': best_streak >= 30,
        'streak_100': best_streak >= 100,
        'first_complete': total_completions >= 1,
        'fifty_completions': total_completions >= 50,
        'hundred_completions': total_completions >= 100,
        'first_friend': friend_count >= 1,
        'five_friends': friend_count >= 5,
        'perfect_day': perfect_day,
    }

    for key, condition in checks.items():
        if condition and key not in earned_keys:
            ach = Achievement.query.filter_by(key=key).first()
            if ach:
                ua = UserAchievement(user_id=user.id, achievement_id=ach.id)
                db.session.add(ua)
                new_achievements.append(ach)

    if new_achievements:
        db.session.commit()
    return new_achievements

# ========== PERFIL ==========

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """Pagina de perfil del usuario"""
    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'update_profile':
            current_user.bio = request.form.get('bio', '')[:300]
            current_user.avatar_color = request.form.get('avatar_color', '#6366f1')
            current_user.is_public = request.form.get('is_public') == 'on'
            db.session.commit()
            flash('Perfil actualizado', 'success')

        elif action == 'change_password':
            current_pw = request.form.get('current_password', '')
            new_pw = request.form.get('new_password', '')
            confirm_pw = request.form.get('confirm_password', '')
            if not current_user.check_password(current_pw):
                flash('Contrasena actual incorrecta', 'error')
            elif len(new_pw) < 6:
                flash('La nueva contrasena debe tener al menos 6 caracteres', 'error')
            elif new_pw != confirm_pw:
                flash('Las contrasenas no coinciden', 'error')
            else:
                current_user.set_password(new_pw)
                db.session.commit()
                flash('Contrasena actualizada', 'success')

        return redirect(url_for('profile'))

    # Stats
    total_habits = Habit.query.filter_by(user_id=current_user.id).count()
    total_completions = Completion.query.join(Habit).filter(Habit.user_id == current_user.id).count()
    best_streak = db.session.query(db.func.max(Habit.best_streak)).filter(Habit.user_id == current_user.id).scalar() or 0
    friends = current_user.get_friends()

    # Check achievements
    new_achs = check_achievements(current_user)
    if new_achs:
        for a in new_achs:
            flash(f'Nuevo logro: {a.name}!', 'success')

    all_achievements = Achievement.query.all()
    earned_ids = {ua.achievement_id for ua in current_user.achievements}

    return render_template('profile.html',
                         total_habits=total_habits,
                         total_completions=total_completions,
                         best_streak=best_streak,
                         friends=friends,
                         all_achievements=all_achievements,
                         earned_ids=earned_ids)

# ========== AMIGOS ==========

@app.route('/friends')
@login_required
def friends_page():
    """Pagina de amigos"""
    friends = current_user.get_friends()
    pending = current_user.get_pending_received()

    # Check achievements
    check_achievements(current_user)

    return render_template('friends.html', friends=friends, pending=pending)

@app.route('/friends/search')
@login_required
def search_users():
    """Buscar usuarios para agregar como amigos"""
    q = request.args.get('q', '').strip()
    results = []
    if len(q) >= 2:
        results = User.query.filter(
            User.username.ilike(f'%{q}%'),
            User.id != current_user.id
        ).limit(20).all()

        # Add friendship status to each result
        for u in results:
            u.friendship_status = None
            f = current_user.friendship_with(u.id)
            if f:
                u.friendship_status = f.status
                u.friendship_sender_id = f.user_id

    return render_template('friends.html',
                         friends=current_user.get_friends(),
                         pending=current_user.get_pending_received(),
                         search_results=results,
                         search_query=q)

@app.route('/friends/add/<int:user_id>', methods=['POST'])
@login_required
def send_friend_request(user_id):
    """Enviar solicitud de amistad"""
    if user_id == current_user.id:
        flash('No puedes agregarte a ti mismo', 'error')
        return redirect(url_for('friends_page'))

    existing = current_user.friendship_with(user_id)
    if existing:
        flash('Ya tienes una solicitud con este usuario', 'info')
        return redirect(url_for('friends_page'))

    target = User.query.get_or_404(user_id)
    friendship = Friendship(user_id=current_user.id, friend_id=target.id, status='pending')
    db.session.add(friendship)
    db.session.commit()

    flash(f'Solicitud enviada a {target.username}', 'success')
    return redirect(url_for('friends_page'))

@app.route('/friends/accept/<int:friendship_id>', methods=['POST'])
@login_required
def accept_friend(friendship_id):
    """Aceptar solicitud de amistad"""
    f = Friendship.query.get_or_404(friendship_id)
    if f.friend_id != current_user.id:
        flash('No autorizado', 'error')
        return redirect(url_for('friends_page'))

    f.status = 'accepted'
    db.session.commit()

    # Check social achievements for both users
    check_achievements(current_user)
    check_achievements(f.sender)

    flash(f'Ahora eres amigo de {f.sender.username}!', 'success')
    return redirect(url_for('friends_page'))

@app.route('/friends/reject/<int:friendship_id>', methods=['POST'])
@login_required
def reject_friend(friendship_id):
    """Rechazar solicitud de amistad"""
    f = Friendship.query.get_or_404(friendship_id)
    if f.friend_id != current_user.id:
        flash('No autorizado', 'error')
        return redirect(url_for('friends_page'))

    db.session.delete(f)
    db.session.commit()
    flash('Solicitud rechazada', 'info')
    return redirect(url_for('friends_page'))

@app.route('/friends/remove/<int:user_id>', methods=['POST'])
@login_required
def remove_friend(user_id):
    """Eliminar amigo"""
    f = current_user.friendship_with(user_id)
    if f:
        db.session.delete(f)
        db.session.commit()
        flash('Amigo eliminado', 'info')
    return redirect(url_for('friends_page'))

# ========== PERFIL PÚBLICO ==========

@app.route('/user/<username>')
@login_required
def public_profile(username):
    """Ver perfil publico de un usuario"""
    user = User.query.filter_by(username=username).first_or_404()

    if not user.is_public and user.id != current_user.id:
        flash('Este perfil es privado', 'info')
        return redirect(url_for('friends_page'))

    total_habits = Habit.query.filter_by(user_id=user.id).count()
    total_completions = Completion.query.join(Habit).filter(Habit.user_id == user.id).count()
    best_streak = db.session.query(db.func.max(Habit.best_streak)).filter(Habit.user_id == user.id).scalar() or 0
    active_habits = Habit.query.filter_by(user_id=user.id, is_active=True).count()

    # Get user's earned achievements
    earned_achievements = UserAchievement.query.filter_by(user_id=user.id).all()

    # Top habits by streak
    top_habits = Habit.query.filter_by(user_id=user.id, is_active=True).order_by(Habit.best_streak.desc()).limit(5).all()

    # Friendship status
    friendship = current_user.friendship_with(user.id) if current_user.id != user.id else None

    # Days since joined
    days_member = (datetime.utcnow() - user.created_at).days if user.created_at else 0

    return render_template('public_profile.html',
                         profile_user=user,
                         total_habits=total_habits,
                         total_completions=total_completions,
                         best_streak=best_streak,
                         active_habits=active_habits,
                         earned_achievements=earned_achievements,
                         top_habits=top_habits,
                         friendship=friendship,
                         days_member=days_member)

# ========== LEADERBOARD ==========

@app.route('/leaderboard')
@login_required
def leaderboard():
    """Leaderboard de amigos"""
    friends = current_user.get_friends()
    friend_ids = [f.id for f in friends] + [current_user.id]

    leaderboard_data = []
    for uid in friend_ids:
        u = User.query.get(uid)
        if not u:
            continue
        streak = db.session.query(db.func.max(Habit.best_streak)).filter(Habit.user_id == uid).scalar() or 0
        completions = Completion.query.join(Habit).filter(Habit.user_id == uid).count()
        today_done = Completion.query.join(Habit).filter(
            Habit.user_id == uid,
            db.func.date(Completion.completed_date) == date.today()
        ).count()
        ach_count = UserAchievement.query.filter_by(user_id=uid).count()

        leaderboard_data.append({
            'user': u,
            'best_streak': streak,
            'total_completions': completions,
            'today_done': today_done,
            'achievements': ach_count,
            'is_me': uid == current_user.id
        })

    # Sort by total completions descending
    leaderboard_data.sort(key=lambda x: x['total_completions'], reverse=True)

    return render_template('leaderboard.html', leaderboard=leaderboard_data)

# ========== API PARA GRÁFICAS ==========

@app.route('/api/chart/completions')
@login_required
def api_chart_completions():
    """Completaciones de los ultimos 30 dias para Chart.js"""
    from datetime import timedelta
    today = date.today()
    data = []
    for i in range(29, -1, -1):
        d = today - timedelta(days=i)
        count = Completion.query.join(Habit).filter(
            Habit.user_id == current_user.id,
            db.func.date(Completion.completed_date) == d
        ).count()
        data.append({'date': d.strftime('%d/%m'), 'count': count})
    return jsonify(data)

@app.route('/api/chart/heatmap')
@login_required
def api_chart_heatmap():
    """Datos para heatmap de los ultimos 365 dias"""
    from datetime import timedelta
    today = date.today()
    data = {}
    for i in range(364, -1, -1):
        d = today - timedelta(days=i)
        count = Completion.query.join(Habit).filter(
            Habit.user_id == current_user.id,
            db.func.date(Completion.completed_date) == d
        ).count()
        data[d.isoformat()] = count
    return jsonify(data)

@app.route('/health')
def health():
    return {'status': 'ok', 'message': 'HabitIQ funcionando'}

# Función para crear tablas
def create_tables():
    try:
        with app.app_context():
            db.create_all()
            seed_achievements()
            print("✅ Tablas y logros creados")
    except Exception as e:
        print("⚠️ No se pudieron crear las tablas en create_tables():", str(e))
        print("Continuando sin inicializar la DB. Revisa la conexión a Supabase.")

if __name__ == '__main__':
    # Crear tablas si no existen (comentado temporalmente por problemas de conexión a Supabase)
    # create_tables()
    
    db_url = app.config['SQLALCHEMY_DATABASE_URI']
    db_type = "PostgreSQL (Supabase)" if "postgresql" in db_url else "SQLite (local)"
    
    print("=" * 50)
    print("🚀 HABITIQ - Servidor iniciando")
    print("=" * 50)
    print(f"📁 Base de datos: {db_type}")
    print("🌐 URL: http://localhost:5000")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=5000, debug=True)