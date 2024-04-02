# app.py

import os
import secrets
import string
import random
from PIL import Image
from flask import render_template, url_for, flash, redirect, request, abort
from pass_gn.forms import RegistrationForm, LoginForm, UpdateAccountForm
from pass_gn import app, db, bcrypt
from pass_gn.models import User, Password
from flask_login import login_user, current_user, logout_user, login_required

def generate_password(length=12, include_numbers=True, include_lowercase=True, include_uppercase=True, include_symbols=True):
    """Generate a random password based on user preferences."""
    characters = ''
    if include_numbers:
        characters += string.digits
    if include_lowercase:
        characters += string.ascii_lowercase
    if include_uppercase:
        characters += string.ascii_uppercase
    if include_symbols:
        characters += string.punctuation

    password = ''.join(random.choice(characters) for _ in range(length))
    return password

@app.route("/", methods=['GET', 'POST'])
@app.route("/home", methods=['GET', 'POST'])
def home():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        length = request.form.get('length', '')
        if not length.isdigit():
            flash("Please enter a valid number for password length.", 'danger')
            return redirect(url_for('home'))

        length = int(length)
        if length < 6 or length > 50:
            flash("Password length must be between 6 and 50 characters.", 'danger')
            return redirect(url_for('home'))

        include_numbers = 'numbers' in request.form
        include_lowercase = 'lowercase' in request.form
        include_uppercase = 'uppercase' in request.form
        include_symbols = 'symbols' in request.form

        if not (include_numbers or include_lowercase or include_uppercase or include_symbols):
            flash("Please select at least one option for password composition.", 'danger')
            return redirect(url_for('home'))

        if not include_numbers:
            flash("Password without numbers may be weak. Are you sure?", 'warning')

        password = generate_password(length, include_numbers, include_lowercase, include_uppercase, include_symbols)
        return redirect(url_for('generated_password', password=password))

    return render_template('home.html')

@app.route('/generated_password/<password>')
def generated_password(password):
    return render_template('generated_password.html', password=password)

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    if request.method == 'POST':
        length = request.form.get('length', '')
        if not length.isdigit():
            flash("Please enter a valid number for password length.", 'danger')
            return redirect(url_for('dashboard'))

        length = int(length)
        if length < 6 or length > 50:
            flash("Password length must be between 6 and 50 characters.", 'danger')
            return redirect(url_for('dashboard'))

        include_numbers = 'numbers' in request.form
        include_lowercase = 'lowercase' in request.form
        include_uppercase = 'uppercase' in request.form
        include_symbols = 'symbols' in request.form

        if not (include_numbers or include_lowercase or include_uppercase or include_symbols):
            flash("Please select at least one option for password composition.", 'danger')
            return redirect(url_for('dashboard'))

        if not include_numbers:
            flash("Password without numbers may be weak. Are you sure?", 'warning')

        password = generate_password(length, include_numbers, include_lowercase, include_uppercase, include_symbols)
        new_password = Password(
            password=password,
            include_numbers=include_numbers,
            include_lowercase=include_lowercase,
            include_uppercase=include_uppercase,
            include_symbols=include_symbols,
            user_id=current_user.id
        )
        db.session.add(new_password)
        db.session.commit()
        passwords = Password.query.filter_by(user_id=current_user.id).all()
        
        return redirect(url_for('dashboard_password', password=password, passwords=passwords))
    else:
        passwords = Password.query.filter_by(user_id=current_user.id).all()
        
        return render_template('dashboard.html', passwords=passwords)

@app.route('/dashboard_password/<password>')
def dashboard_password(password):
    passwords = Password.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard_password.html', password=password, passwords=passwords)

@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))

def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)
    
    output_size = (125, 125)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    
    i.save(picture_path)

    return picture_fn

@app.route("/account", methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('account.html', title='Account', image_file=image_file, form=form)

@app.route("/delete_password/<int:password_id>", methods=['POST'])
@login_required
def delete_password(password_id):
    password = Password.query.get_or_404(password_id)
    if password.author != current_user:
        abort(403)
    db.session.delete(password)
    db.session.commit()
    if password not in current_user.passwords:
        flash('Password deleted successfully!', 'success')
    return redirect(url_for('dashboard'))
