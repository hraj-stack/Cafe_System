from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from flask_login import login_user, logout_user, login_required, current_user
from models import db, bcrypt
from models.user import User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.role == 'Admin':
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('customer.dashboard'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False
        user = User.query.filter_by(email=email).first()
        
        if user and bcrypt.check_password_hash(user.password_hash, password):
            login_user(user, remember=remember)
            next_page = request.args.get('next')
            if user.role == 'Admin':
                return redirect(next_page) if next_page else redirect(url_for('admin.dashboard'))
            return redirect(next_page) if next_page else redirect(url_for('customer.dashboard'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
            
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))

    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        
        # Restrict registration to exactly ADMIN_EMAIL and STAFF_EMAIL
        allowed_emails = [current_app.config['ADMIN_EMAIL'], current_app.config['STAFF_EMAIL']]
        if email not in allowed_emails:
            flash('Registration is restricted to authorized setup emails only.', 'danger')
            return redirect(url_for('auth.register'))
        
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already exists. Please log in.', 'warning')
            return redirect(url_for('auth.login'))
            
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        
        # Set role based on configured email
        role = 'Admin' if email == current_app.config['ADMIN_EMAIL'] else 'Customer'
        user = User(name=name, email=email, password_hash=hashed_password, role=role)
        db.session.add(user)
        db.session.commit()
        
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('auth/register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.home'))
