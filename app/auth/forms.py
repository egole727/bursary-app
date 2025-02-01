from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from app.models import User, Profile, Ward
from .validators import validate_password


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember_me = BooleanField("Remember Me")
    submit = SubmitField("Sign In")


class RegistrationForm(FlaskForm):
    first_name = StringField(
        "First Name", validators=[DataRequired(), Length(min=2, max=50)]
    )
    last_name = StringField(
        "Last Name", validators=[DataRequired(), Length(min=2, max=50)]
    )
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    password2 = PasswordField(
        "Confirm Password", validators=[DataRequired(), EqualTo("password")]
    )
    first_name = StringField("First Name", validators=[DataRequired()])
    last_name = StringField("Last Name", validators=[DataRequired()])
    id_number = StringField(
        "Registration Number", validators=[DataRequired(), Length(max=13)]
    )
    phone_number = StringField(
        "Phone Number", validators=[DataRequired(), Length(min=10, max=20)]
    )
    ward_id = SelectField("Ward", coerce=int, validators=[DataRequired()])
    submit = SubmitField("Register")

    def __init__(self, *args, **kwargs):
        super(RegistrationForm, self).__init__(*args, **kwargs)
        self.ward_id.choices = [
            (ward.id, ward.name) for ward in Ward.query.order_by(Ward.name).all()
        ]

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError("Please use a different email address.")

    def validate_id_number(self, id_number):
        profile = Profile.query.filter_by(id_number=id_number.data).first()
        if profile is not None:
            raise ValidationError("This ID number is already registered.")

    def validate_password(self, field):
        """Validate password strength"""
        is_valid, message = validate_password(field.data)
        if not is_valid:
            raise ValidationError(message)


class ForgotPasswordForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    submit = SubmitField("Send Reset Link")

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is None:
            raise ValidationError("No account found with that email address.")


class ResetPasswordForm(FlaskForm):
    password = PasswordField(
        "New Password",
        validators=[
            DataRequired(),
            Length(min=8, message="Password must be at least 8 characters long"),
        ],
    )
    password2 = PasswordField(
        "Confirm New Password",
        validators=[
            DataRequired(),
            EqualTo("password", message="Passwords must match"),
        ],
    )
    submit = SubmitField("Reset Password")

    def validate_password(self, field):
        """Validate password strength"""
        is_valid, message = validate_password(field.data)
        if not is_valid:
            raise ValidationError(message)
