from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from models import db, User

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration endpoint."""
    if request.method == 'GET':
        return render_template('register.html')
    
    data = request.get_json() if request.is_json else request.form
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    
    # Validation
    if not username or not email or not password:
        if request.is_json:
            return jsonify({'error': 'All fields are required'}), 400
        flash('All fields are required', 'error')
        return redirect(url_for('auth.register'))
    
    # Check if user already exists
    if User.query.filter_by(email=email).first():
        if request.is_json:
            return jsonify({'error': 'Email already registered'}), 400
        flash('Email already registered', 'error')
        return redirect(url_for('auth.register'))
    
    if User.query.filter_by(username=username).first():
        if request.is_json:
            return jsonify({'error': 'Username already taken'}), 400
        flash('Username already taken', 'error')
        return redirect(url_for('auth.register'))
    
    # Create new user
    user = User(username=username, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    
    if request.is_json:
        return jsonify({'message': 'Registration successful', 'user': {'username': username, 'email': email}}), 201
    
    flash('Registration successful! Please log in.', 'success')
    return redirect(url_for('auth.login'))


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login endpoint."""
    if request.method == 'GET':
        return render_template('login.html')
    
    data = request.get_json() if request.is_json else request.form
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        if request.is_json:
            return jsonify({'error': 'Email and password are required'}), 400
        flash('Email and password are required', 'error')
        return redirect(url_for('auth.login'))
    
    user = User.query.filter_by(email=email).first()
    
    if user and user.check_password(password):
        login_user(user, remember=True)
        if request.is_json:
            return jsonify({'message': 'Login successful', 'user': {'username': user.username, 'email': user.email}}), 200
        return redirect(url_for('home.index'))
    
    if request.is_json:
        return jsonify({'error': 'Invalid email or password'}), 401
    flash('Invalid email or password', 'error')
    return redirect(url_for('auth.login'))


@auth_bp.route('/logout', methods=['POST', 'GET'])
@login_required
def logout():
    """User logout endpoint."""
    logout_user()
    if request.is_json:
        return jsonify({'message': 'Logout successful'}), 200
    return redirect(url_for('auth.login'))
