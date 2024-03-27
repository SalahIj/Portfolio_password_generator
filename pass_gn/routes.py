from flask import render_template, url_for, flash, redirect, request
from pass_gn.forms import RegistrationForm, LoginForm, UpdateAccountForm
from pass_gn import app, db, bcrypt
import random
import string
from datetime import datetime
from pass_gn.models import User, Password
from flask_login import login_user, current_user, logout_user, login_required



def generate_password(length=0, include_numbers=True, include_lowercase=True, include_uppercase=True, include_symbols=True):
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
    # Check if the user is authenticated (logged in)
    if current_user.is_authenticated:
        # If authenticated, route to the dashboard
        return redirect(url_for('dashboard'))

    # If the request method is POST, generate a temporary password
    if request.method == 'POST':
        length = int(request.form.get('length', 0))
        include_numbers = 'numbers' in request.form
        include_lowercase = 'lowercase' in request.form
        include_uppercase = 'uppercase' in request.form
        include_symbols = 'symbols' in request.form

        if not (include_numbers or include_lowercase or include_uppercase or include_symbols):
            flash("Please select at least one option for password composition.", 'danger')
            return redirect(url_for('home'))

        password = generate_password(length, include_numbers, include_lowercase, include_uppercase, include_symbols)
        return render_template('home.html', password=password)

    # If the request method is GET, render the home page
    return render_template('home.html')


@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if request.method == 'POST':
        length = int(request.form.get('length', 0))
        include_numbers = 'numbers' in request.form
        include_lowercase = 'lowercase' in request.form
        include_uppercase = 'uppercase' in request.form
        include_symbols = 'symbols' in request.form

        if not (include_numbers or include_lowercase or include_uppercase or include_symbols):
            flash("Please select at least one option for password composition.", 'danger')
            return redirect(url_for('dashboard'))

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
        
        return render_template('dashboard.html', password=password, passwords=passwords)
    else:
        # Query passwords from the database for the current user
        passwords = Password.query.filter_by(user_id=current_user.id).all()
        
        # Render the dashboard template with passwords
        return render_template('dashboard.html', passwords=passwords)


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
        flash('Your account has been created! you are now able to log in.', 'success')
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
    return render_template('account.html', title='Account',
                           image_file=image_file, form=form)

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
