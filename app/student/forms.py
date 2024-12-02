from flask_wtf import FlaskForm
from flask_wtf.file import FileField, MultipleFileField
from wtforms import StringField, TextAreaField, DecimalField, DateField, SelectField
from wtforms.validators import DataRequired, Length, NumberRange, Optional
from app.models import Ward

class ProfileForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=50)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=50)])
    date_of_birth = DateField('Date of Birth', validators=[DataRequired()])
    gender = SelectField('Gender', choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')])
    phone_number = StringField('Phone Number', validators=[DataRequired(), Length(max=15)])
    ward_id = SelectField('Ward', coerce=int, validators=[DataRequired()])
    id_number = StringField('ID Number', validators=[DataRequired(), Length(max=15)])

    def __init__(self, *args, **kwargs):
        super(ProfileForm, self).__init__(*args, **kwargs)
        self.ward_id.choices = [(0, 'Select Ward')] + [
            (ward.id, ward.name) for ward in Ward.query.order_by(Ward.name).all()
        ]

class AcademicInfoForm(FlaskForm):
    school_name = StringField('School Name', validators=[DataRequired(), Length(max=200)])
    current_grade = StringField('Current Grade/Year', validators=[DataRequired(), Length(max=50)])
    institution = StringField('Institution Name', validators=[DataRequired(), Length(max=100)])
    course = StringField('Course Name', validators=[DataRequired(), Length(max=100)])
    year_of_study = SelectField('Year of Study', 
                              choices=[(1, '1st Year'), (2, '2nd Year'), 
                                     (3, '3rd Year'), (4, '4th Year'),
                                     (5, '5th Year'), (6, '6th Year')],
                              coerce=int)
    student_id = StringField('Student ID', validators=[DataRequired(), Length(max=20)])

class ApplicationForm(FlaskForm):
    amount = DecimalField('Amount Requested (KES)', 
                         validators=[DataRequired(), NumberRange(min=0)],
                         places=2)
    reason = TextAreaField('Reason for Application', 
                          validators=[DataRequired(), Length(min=100, max=1000)])
    documents = MultipleFileField('Supporting Documents')
