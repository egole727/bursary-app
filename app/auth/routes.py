from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, current_user, login_required
from urllib.parse import urlparse
from datetime import datetime, timedelta
from app import db
from app.auth import bp
from app.auth.forms import (
    LoginForm,
    RegistrationForm,
    ForgotPasswordForm,
    ResetPasswordForm,
)
from app.models import User, Profile, Ward
from app.email import send_verification_email, send_password_reset_email
from sqlalchemy.exc import IntegrityError
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature


def generate_verification_token(email):
    serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    return serializer.dumps(email, salt="email-verification")


def generate_password_reset_token(email):
    serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
    return serializer.dumps(email, salt="password-reset")


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        if current_user.role == "ADMIN":
            return redirect(url_for("admin.dashboard"))
        elif current_user.role == "WARD_ADMIN":
            return redirect(url_for("ward_admin.dashboard"))
        else:
            return redirect(url_for("student.dashboard"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash("Invalid email or password", "error")
            return redirect(url_for("auth.login"))

        if not user.email_verified:
            flash(
                "Please verify your email before logging in. Check your inbox for the verification link.",
                "warning",
            )
            return redirect(url_for("auth.login"))

        login_user(user, remember=form.remember_me.data)

        if user.role == "ADMIN":
            return redirect(url_for("admin.dashboard"))
        elif user.role == "WARD_ADMIN":
            return redirect(url_for("ward_admin.dashboard"))
        else:
            return redirect(url_for("student.dashboard"))

    return render_template("auth/login.html", title="Sign In", form=form)


@bp.route("/verify-email/<token>")
def verify_email(token):
    try:
        serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
        email = serializer.loads(
            token, salt="email-verification", max_age=86400
        )  # 24 hours

        user = User.query.filter_by(email=email).first()
        if user is None:
            flash("Invalid verification link.", "error")
            return redirect(url_for("main.index"))

        if user.email_verified:
            flash("Email already verified.", "info")
            return redirect(url_for("auth.login"))

        user.email_verified = True
        user.email_verification_token = None
        db.session.commit()

        flash("Your email has been verified. You can now log in.", "success")
        return redirect(url_for("auth.login"))
    except (SignatureExpired, BadTimeSignature):
        flash("The verification link is invalid or has expired.", "error")
        return redirect(url_for("main.index"))


@bp.route("/verify-pending")
def verify_pending():
    email = request.args.get("email")
    if not email:
        return redirect(url_for("main.index"))
    return render_template("auth/verify_pending.html", email=email)


@bp.route("/resend-verification", methods=["POST"])
def resend_verification():
    email = request.form.get("email")
    if not email:
        flash("Email address is required.", "error")
        return redirect(url_for("auth.login"))

    user = User.query.filter_by(email=email).first()
    if not user:
        flash("Invalid email address.", "error")
        return redirect(url_for("auth.login"))

    if user.email_verified:
        flash("Email is already verified. Please login.", "info")
        return redirect(url_for("auth.login"))

    # Generate new verification token
    token = generate_verification_token(user.email)
    user.email_verification_token = token
    user.email_verification_sent_at = datetime.utcnow()
    db.session.commit()

    # Send new verification email
    try:
        send_verification_email(user, token)
        flash(
            "A new verification email has been sent. Please check your inbox.",
            "success",
        )
    except Exception as e:
        flash("Failed to send verification email. Please try again later.", "error")
        print(f"Email error: {str(e)}")

    return redirect(url_for("auth.verify_pending", email=email))


@bp.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("main.index"))


@bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    form = RegistrationForm()
    if form.validate_on_submit():
        try:
            # Check if email already exists
            existing_user = User.query.filter_by(email=form.email.data).first()
            if existing_user:
                print(f"Found existing user with email {form.email.data}")
                flash("Error: Email already registered.", "error")
                return redirect(url_for("auth.register"))

            # Check if username (email) already exists
            existing_username = User.query.filter_by(username=form.email.data).first()
            if existing_username:
                print(f"Found existing username {form.email.data}")
                flash("Error: Email already taken as username.", "error")
                return redirect(url_for("auth.register"))

            # Check if ID number already exists
            existing_id = Profile.query.filter_by(id_number=form.id_number.data).first()
            if existing_id:
                print(f"Found existing ID number {form.id_number.data}")
                flash("Error: ID number already registered.", "error")
                return redirect(url_for("auth.register"))

            # Check if phone number already exists
            existing_phone = Profile.query.filter_by(
                phone_number=form.phone_number.data
            ).first()
            if existing_phone:
                print(f"Found existing phone number {form.phone_number.data}")
                flash("Error: Phone number already registered.", "error")
                return redirect(url_for("auth.register"))

            print(f"Creating new user with email: {form.email.data}")
            user = User(
                email=form.email.data,
                username=form.email.data,  # Using email as username
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                role="STUDENT",
            )
            user.set_password(form.password.data)

            # Generate and set verification token
            token = generate_verification_token(user.email)
            user.email_verification_token = token
            user.email_verification_sent_at = datetime.utcnow()

            db.session.add(user)

            # Create profile with all required fields
            profile = Profile(
                user=user,
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                phone_number=form.phone_number.data,
                id_number=form.id_number.data,
                ward_id=form.ward_id.data,
            )

            db.session.add(profile)

            try:
                db.session.commit()
                print(f"Successfully created user and profile for {form.email.data}")
            except Exception as e:
                db.session.rollback()
                print(f"Database error during commit: {str(e)}")
                flash("Registration failed. Please try again.", "error")
                return redirect(url_for("auth.register"))

            # Send verification email
            try:
                send_verification_email(user, token)
                flash(
                    "Registration successful! Please check your email to verify your account.",
                    "success",
                )
            except Exception as e:
                flash(
                    "Registration successful but failed to send verification email. Please try again later.",
                    "warning",
                )
                print(f"Email error: {str(e)}")

            return redirect(url_for("auth.verify_pending", email=user.email))

        except Exception as e:
            db.session.rollback()
            print(f"Unexpected error during registration: {str(e)}")
            flash("Registration failed. Please try again.", "error")
            return redirect(url_for("auth.register"))

    return render_template("auth/register.html", title="Register", form=form)


@bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    form = ForgotPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            token = generate_password_reset_token(user.email)
            user.password_reset_token = token
            user.password_reset_expires = datetime.utcnow() + timedelta(hours=24)
            db.session.commit()

            try:
                send_password_reset_email(user, token)
                flash(
                    "Check your email for instructions to reset your password.", "info"
                )
            except Exception as e:
                print(f"Error sending password reset email: {str(e)}")
                flash(
                    "Error sending password reset email. Please try again later.",
                    "error",
                )

            return redirect(url_for("auth.login"))

        flash(
            "If an account exists with that email, a password reset link has been sent.",
            "info",
        )
        return redirect(url_for("auth.login"))

    return render_template(
        "auth/forgot_password.html", title="Reset Password", form=form
    )


@bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    try:
        serializer = URLSafeTimedSerializer(current_app.config["SECRET_KEY"])
        email = serializer.loads(
            token, salt="password-reset", max_age=86400
        )  # 24 hours
        user = User.query.filter_by(email=email).first()

        if user is None:
            flash("Invalid or expired reset link.", "error")
            return redirect(url_for("auth.forgot_password"))

        if (
            user.password_reset_token != token
            or user.password_reset_expires is None
            or user.password_reset_expires < datetime.utcnow()
        ):
            flash("Invalid or expired reset link.", "error")
            return redirect(url_for("auth.forgot_password"))

    except (SignatureExpired, BadTimeSignature):
        flash("Invalid or expired reset link.", "error")
        return redirect(url_for("auth.forgot_password"))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        user.password_reset_token = None
        user.password_reset_expires = None
        db.session.commit()
        flash("Your password has been reset.", "success")
        return redirect(url_for("auth.login"))

    return render_template(
        "auth/reset_password.html", title="Reset Password", form=form
    )
