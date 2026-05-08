import os
from datetime import timedelta
from flask import Flask, render_template, request, session, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy

# ==========================================
# 1. APP INITIALIZATION & CONFIGURATION
# ==========================================
app = Flask(__name__)

# Security Key for Sessions
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'el_rosie_secret_9988')
app.permanent_session_lifetime = timedelta(days=31)

# DATABASE PATH SETUP (Fixed for Render)
basedir = os.path.abspath(os.path.dirname(__file__))
# This creates a folder named 'instance' if it doesn't exist
instance_path = os.path.join(basedir, 'instance')
if not os.path.exists(instance_path):
    os.makedirs(instance_path)

# Pointing the database to the instance folder
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(instance_path, 'users.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# ==========================================
# 2. DATABASE SETUP & MODELS
# ==========================================
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), default='customer')

# ==========================================
# 3. ROUTES (LOGIC)
# ==========================================

@app.route('/')
def home():
    # Make sure your main html file is named 'index.html' or change this line
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Check if user already exists in the database
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email already exists. Please login instead.", "warning")
            return redirect(url_for('login'))
        
        # Create new user and save to the .db file
        new_user = User(email=email, password=password, role='customer')
        db.session.add(new_user)
        db.session.commit() # This saves it permanently!
        
        flash("Account created! Please log in.", "success")
        return redirect(url_for('login'))
        
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Search the database for this email
        user = User.query.filter_by(email=email).first()
        
        # Check if user exists and password matches
        if user and user.password == password:
            session.permanent = True
            session['user'] = user.email
            session['role'] = user.role
            
            flash(f"Welcome back to El Rosie!", "success")
            
            if user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('home'))
        else:
            # This is what your classmate was seeing!
            flash("Invalid email or password. Please try again.", "danger")
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))

@app.route('/admin_dashboard')
def admin_dashboard():
    # Only allow 'admin' users to see this page
    if session.get('role') != 'admin':
        flash("Access Denied: Admins only.", "danger")
        return redirect(url_for('home'))
    return "<h1>Welcome to the Admin Dashboard</h1><p>Only admins see this.</p>"

# ==========================================
# 4. EXECUTION
# ==========================================
if __name__ == '__main__':
    with app.app_context():
        # This line automatically creates 'users.db' if it's missing
        db.create_all()
    app.run(debug=True)