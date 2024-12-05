from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, TextAreaField, DecimalField, DateField, SelectField, SubmitField, PasswordField, EmailField
from wtforms.validators import DataRequired, Length, NumberRange, ValidationError, Optional, Email
from datetime import date, datetime
from app.models import Ward, User

class BursaryProgramForm(FlaskForm):
    name = StringField('Program Name', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Description', validators=[DataRequired()])
    start_date = DateField('Start Date', validators=[DataRequired()])
    end_date = DateField('End Date', validators=[DataRequired()])
    amount = DecimalField('Amount (KES)', validators=[DataRequired(), NumberRange(min=0)])
    ward_id = SelectField('Ward', coerce=int, validators=[Optional()])
    submit = SubmitField('Submit')

    def __init__(self, *args, **kwargs):
        super(BursaryProgramForm, self).__init__(*args, **kwargs)
        self.ward_id.choices = [(-1, 'All Wards')] + [
            (ward.id, ward.name) for ward in Ward.query.order_by(Ward.name).all()
        ]

    def validate_start_date(self, field):
        if field.data < datetime.now().date():
            raise ValidationError('Start date cannot be in the past')

    def validate_end_date(self, field):
        if field.data < self.start_date.data:
            raise ValidationError('End date must be after start date')

class WardForm(FlaskForm):
    name = StringField('Ward Name', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[DataRequired(), Length(max=500)])
    total_budget = DecimalField('Total Budget (KES)', validators=[DataRequired(), NumberRange(min=0)])
    submit = SubmitField('Submit')

class ApplicationReviewForm(FlaskForm):
    status = SelectField('Decision', choices=[
        ('APPROVED', 'Approve Application'),
        ('REJECTED', 'Reject Application'),
        ('PENDING', 'Keep Pending'),
        ('INFO_REQUESTED', 'Request More Information')
    ], validators=[DataRequired()])
    comments = TextAreaField('Comments', validators=[DataRequired(), Length(min=10)])
    submit = SubmitField('Submit Review')

class DocumentForm(FlaskForm):
    name = StringField('Document Name', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[Length(max=500)])
    file = FileField('Document', validators=[
        FileRequired(),
        FileAllowed(['pdf', 'doc', 'docx'], 'Only PDF and Word documents are allowed!')
    ])
    submit = SubmitField('Upload Document')

class WardAdminForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=64)])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    ward_id = SelectField('Ward', coerce=int, validators=[DataRequired()])

    def __init__(self, *args, **kwargs):
        super(WardAdminForm, self).__init__(*args, **kwargs)
        self.ward_id.choices = [(0, 'Select Ward')] + [
            (ward.id, ward.name) for ward in Ward.query.order_by(Ward.name).all()
        ]

    def validate_username(self, field):
        user = User.query.filter_by(username=field.data).first()
        if user:
            raise ValidationError('Username already exists.')

    def validate_email(self, field):
        user = User.query.filter_by(email=field.data).first()
        if user:
            raise ValidationError('Email already registered.')
