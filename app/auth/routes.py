from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user, login_required
from urllib.parse import urlparse
from app import db
from app.auth import bp
from app.auth.forms import LoginForm, RegistrationForm
from app.models import User, Profile, Ward
from sqlalchemy.exc import IntegrityError

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if current_user.role == 'ADMIN':
            return redirect(url_for('admin.dashboard'))
        elif current_user.role == 'WARD_ADMIN':
            return redirect(url_for('ward_admin.dashboard'))
        else:
            return redirect(url_for('student.dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid email or password', 'error')
            return redirect(url_for('auth.login'))
        
        login_user(user, remember=form.remember_me.data)
        
        if user.role == 'ADMIN':
            return redirect(url_for('admin.dashboard'))
        elif user.role == 'WARD_ADMIN':
            return redirect(url_for('ward_admin.dashboard'))
        else:
            return redirect(url_for('student.dashboard'))
    
    return render_template('auth/login.html', title='Sign In', form=form)

@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            # Create user with username (using email as username)
            user = User(
                username=form.email.data,
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                email=form.email.data,
                role='STUDENT'
            )
            user.set_password(form.password.data)
            
            # Create profile
            profile = Profile(
                user=user,
                phone_number=form.phone_number.data,
                id_number=form.id_number.data,
                ward_id=form.ward_id.data if hasattr(form, 'ward_id') else None
            )
            
            db.session.add(user)
            db.session.add(profile)
            db.session.commit()
            
            flash('Congratulations, you are now registered!', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            db.session.rollback()
            flash('Registration failed. Please try again.', 'error')
            print(f"Registration error: {str(e)}")  # For debugging
            
    return render_template('auth/register.html', title='Register', form=form)
