from functools import wraps
from flask import flash, redirect, url_for, abort
from flask_login import current_user

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if not current_user.is_admin:
            flash('Access denied. You do not have administrator privileges.', 'danger')
            if current_user.is_authenticated:
                return redirect(url_for('student.dashboard'))
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

def student_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if current_user.is_admin:
            flash('This page is for students only.', 'danger')
            return redirect(url_for('admin.dashboard'))
        return f(*args, **kwargs)
    return decorated_function
