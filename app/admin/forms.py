from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, TextAreaField, DecimalField, DateField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange, ValidationError
from datetime import date, datetime

class BursaryProgramForm(FlaskForm):
    name = StringField('Program Name', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[DataRequired(), Length(max=500)])
    start_date = DateField('Start Date', validators=[DataRequired()], format='%Y-%m-%d')
    end_date = DateField('End Date', validators=[DataRequired()], format='%Y-%m-%d')
    amount = DecimalField('Amount (KES)', validators=[DataRequired(), NumberRange(min=0)])
    ward_id = SelectField('Ward', validators=[DataRequired()], coerce=int)
    submit = SubmitField('Submit')

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
