import sys
import os
from flask import Blueprint, request, jsonify, render_template, session, redirect, url_for
from models import db, User
from werkzeug.security import generate_password_hash, check_password_hash
import re

# Add the current directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

auth = Blueprint('auth', __name__)

@auth.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('auth.login_page'))
    return render_template('index.html')

@auth.route('/login', methods=['GET'])
def login_page():
    return render_template('login.html')

@auth.route('/signup', methods=['GET'])
def signup_page():
    return render_template('signup.html')

@auth.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username_or_email = data.get('usernameOrEmail')
    password = data.get('password')

    if not username_or_email or not password:
        return jsonify({"success": False, "message": "Username/Email and password are required"}), 400

    # Handle hardcoded admin credentials without database operations
    if username_or_email == 'admin' and password == 'jkl;asdf':
        # Set session variables for admin without database operations
        session['user_id'] = -999  # Special ID for hardcoded admin
        session['username'] = 'admin'
        session['is_admin'] = True
        
        return jsonify({"success": True, "username": 'admin', "is_admin": True, "redirect": "/admin"})

    # Regular login flow
    if '@' in username_or_email:
        user = User.query.filter_by(email=username_or_email).first()
    else:
        user = User.query.filter_by(username=username_or_email).first()

    if user and check_password_hash(user.password_hash, password):
        # Check if user is banned
        if hasattr(user, "is_banned") and user.is_banned:
            return jsonify({"success": False, "message": "Your account has been banned"}), 403
        
        session['user_id'] = user.id
        session['username'] = user.username
        session['is_admin'] = user.is_admin if hasattr(user, 'is_admin') else False
        
        # If user is an admin, include redirect info
        if getattr(user, 'is_admin', False):
            return jsonify({"success": True, "username": user.username, "is_admin": True, "redirect": "/admin"})
        
        return jsonify({"success": True, "username": user.username})

    return jsonify({"success": False, "message": "Invalid username/email or password"}), 401

@auth.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    password = data.get('password')

    # Validate input
    if not username or not email or not password:
        return jsonify({"success": False, "message": "Username, email, and password are required"}), 400

    # Check if email is valid
    if not is_valid_email(email):
        return jsonify({"success": False, "message": "Invalid email format"}), 400

    # Check if username or email already exists
    if User.query.filter_by(username=username).first():
        return jsonify({"success": False, "message": "Username already exists"}), 400
    
    if User.query.filter_by(email=email).first():
        return jsonify({"success": False, "message": "Email already exists"}), 400

    # Create new user with password_hash
    new_user = User(username=username, email=email, password_hash=generate_password_hash(password))
    
    db.session.add(new_user)
    db.session.commit()

    # Log in the user after successful registration
    session['user_id'] = new_user.id
    session['username'] = new_user.username

    return jsonify({"success": True, "message": "Registration successful", "username": new_user.username})

@auth.route('/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    return jsonify({"success": True})

@auth.route('/api/logout', methods=['POST'])
def api_logout():
    session.pop('user_id', None)
    session.pop('username', None)
    return jsonify({"success": True})

@auth.route('/api/me', methods=['GET'])
def get_current_user():
    if 'user_id' not in session or 'username' not in session:
        return jsonify({"success": False, "message": "Not logged in"}), 401

    return jsonify({
        "success": True,
        "user": {
            "id": session['user_id'],
            "username": session['username']
        }
    })

@auth.route('/hello')
def hello():
    return "Hello from Flask!"

@auth.route('/health')
def health_check():
    return "OK", 200

def is_valid_email(email):
    # Regular expression for email validation
    email_regex = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    return bool(email_regex.match(email)) 