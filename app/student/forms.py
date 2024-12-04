from flask_wtf import FlaskForm
from flask_wtf.file import FileField, MultipleFileField
from wtforms import StringField, TextAreaField, DecimalField, DateField, SelectField
from wtforms.validators import DataRequired, Length, NumberRange, Optional, ValidationError
from flask_login import current_user
from app.models import Ward, Profile, AcademicInfo

class ProfileForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired(), Length(max=50)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(max=50)])
    date_of_birth = DateField('Date of Birth', validators=[DataRequired()])
    gender = SelectField('Gender', choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')])
    phone_number = StringField('Phone Number', validators=[DataRequired(), Length(max=15)])
    ward_id = SelectField('Ward', coerce=int, validators=[DataRequired()])
    id_number = StringField('ID Number', validators=[DataRequired(), Length(max=15)])

    def validate_phone_number(self, field):
        profile = Profile.query.filter_by(phone_number=field.data).first()
        if profile and (not current_user.profile or profile.id != current_user.profile.id):
            raise ValidationError('This phone number is already registered.')

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

    def validate_student_id(self, field):
        academic = AcademicInfo.query.filter_by(student_id=field.data).first()
        if academic and (not current_user.academic_info or academic.id != current_user.academic_info.id):
            raise ValidationError('This student ID is already registered.')

class ApplicationForm(FlaskForm):
    amount = DecimalField('Amount Requested (KES)', 
                         validators=[DataRequired(), NumberRange(min=0)],
                         places=2)
    reason = TextAreaField('Reason for Application', 
                          validators=[DataRequired(), Length(min=100, max=1000)])
    documents = MultipleFileField('Supporting Documents')
