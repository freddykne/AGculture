from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
from functools import wraps

# Initialisation de l'application Flask
app = Flask(__name__)
app.secret_key = os.urandom(24)

# Configuration de la base de données
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Modèles de la base de données
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)

class Crop(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(80), nullable=False)
    planting_date = db.Column(db.String(10), nullable=False)
    status = db.Column(db.String(20), nullable=False)

# Initialisation de la base de données
def init_db():
    with app.app_context():
        db.create_all()

# Décorateur pour vérifier si l'utilisateur est connecté
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Vous devez vous connecter pour accéder à cette page.')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Routes de l'application
@app.route('/')
def home():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            return redirect(url_for('dashboard'))
        else:
            flash('Nom d\'utilisateur ou mot de passe invalide')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Tous les champs sont obligatoires.')
            return redirect(url_for('register'))

        try:
            new_user = User(username=username, password=generate_password_hash(password))
            db.session.add(new_user)
            db.session.commit()
            flash('Inscription réussie ! Vous pouvez vous connecter.')
        except Exception as e:
            flash(f'Erreur lors de l\'inscription : {str(e)}')
            return redirect(url_for('register'))
        
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/dashboard')
@login_required
def dashboard():
    crops = Crop.query.filter_by(user_id=session['user_id']).all()
    return render_template('dashboard.html', crops=crops)

@app.route('/add_crop', methods=['POST'])
@login_required
def add_crop():
    name = request.form.get('name')
    planting_date = request.form.get('planting_date')
    status = request.form.get('status')
    
    if not name or not planting_date or not status:
        flash('Tous les champs sont obligatoires.')
        return redirect(url_for('dashboard'))

    try:
        new_crop = Crop(user_id=session['user_id'], name=name, planting_date=planting_date, status=status)
        db.session.add(new_crop)
        db.session.commit()
        flash('Culture ajoutée avec succès !')
    except Exception as e:
        flash(f'Erreur lors de l\'ajout de la culture : {str(e)}')
    
    return redirect(url_for('dashboard'))

@app.route('/statistic')
@login_required
def statistic():
    try:
        crops = Crop.query.filter_by(user_id=session['user_id']).all()
        return render_template('statistics.html', crops=crops)
    except Exception as e:
        flash(f'Erreur lors du chargement des statistiques : {str(e)}')
        return redirect(url_for('dashboard'))

if __name__ == '__main__':
    init_db()  # Initialiser la base de données au démarrage
    app.run(debug=True)