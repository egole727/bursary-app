from flask_wtf import FlaskForm
from flask_wtf.file import FileField, MultipleFileField
from wtforms import StringField, TextAreaField, DecimalField, DateField, SelectField
from wtforms.validators import DataRequired, Length, NumberRange, Optional
from app.models import Ward

class ProfileForm(FlaskForm):
    id_number = StringField('ID Number', validators=[DataRequired(), Length(max=20)])
    phone_number = StringField('Phone Number', validators=[DataRequired(), Length(max=20)])
    date_of_birth = DateField('Date of Birth', validators=[DataRequired()])
    gender = SelectField('Gender', choices=[('', 'Select Gender'), ('M', 'Male'), ('F', 'Female')], validators=[DataRequired()])
    address = StringField('Address', validators=[DataRequired(), Length(max=200)])
    ward_id = SelectField('Ward', coerce=int, validators=[DataRequired()])

    def __init__(self, *args, **kwargs):
        super(ProfileForm, self).__init__(*args, **kwargs)
        self.ward_id.choices = [(0, 'Select Ward')] + [
            (ward.id, ward.name) for ward in Ward.query.order_by(Ward.name).all()
        ]

class AcademicInfoForm(FlaskForm):
    school_name = StringField('School Name', validators=[DataRequired(), Length(max=200)])
    current_grade = StringField('Current Grade/Year', validators=[DataRequired(), Length(max=50)])

class ApplicationForm(FlaskForm):
    amount = DecimalField('Amount Requested (KES)', 
                         validators=[DataRequired(), NumberRange(min=0)],
                         places=2)
    reason = TextAreaField('Reason for Application', 
                          validators=[DataRequired(), Length(min=100, max=1000)])
    documents = MultipleFileField('Supporting Documents')
