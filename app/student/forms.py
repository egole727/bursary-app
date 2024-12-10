from flask_wtf import FlaskForm
from flask_wtf.file import FileField, MultipleFileField
from wtforms import StringField, TextAreaField, DecimalField, DateField, SelectField
from wtforms.validators import DataRequired, Length, NumberRange, Optional, ValidationError
from flask_login import current_user
from flask_wtf.file import FileRequired, FileAllowed
from app.models import Ward, Profile, AcademicInfo

class ProfileForm(FlaskForm):
    first_name = StringField('First Name', validators=[DataRequired()])
    last_name = StringField('Last Name', validators=[DataRequired()])
    phone_number = StringField('Phone Number', validators=[DataRequired()])
    id_number = StringField('ID Number', validators=[DataRequired()])
    ward_id = SelectField('Ward', coerce=int, validators=[DataRequired()])
    gender = SelectField('Gender', choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')])

    def populate_from_profile(self, profile):
        if profile:
            self.first_name.data = profile.first_name
            self.last_name.data = profile.last_name
            self.phone_number.data = profile.phone_number
            self.id_number.data = profile.id_number
            self.ward_id.data = profile.ward_id

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
    # Institution Details
    institution_name = StringField('Institution Name', validators=[DataRequired()])
    education_level = SelectField('Education Level', 
                                choices=[
                                    ('secondary', 'Secondary School'),
                                    ('college', 'College'),
                                    ('university', 'University')
                                ],
                                validators=[DataRequired()])
    year_of_study = SelectField('Year of Study',
                               choices=[
                                   ('1', 'First Year'),
                                   ('2', 'Second Year'),
                                   ('3', 'Third Year'),
                                   ('4', 'Fourth Year'),
                                   ('5', 'Fifth Year'),
                                   ('6', 'Sixth Year')
                               ],
                               validators=[DataRequired()])
    student_id = StringField('Student ID/Admission Number', validators=[DataRequired()])
    course = StringField('Course/Program', validators=[Optional()])
    current_grade = StringField('Current Grade/Performance', validators=[Optional()])
    
    # Banking Details
    school_account_number = StringField('School Account Number', validators=[DataRequired()])
    bank_name = StringField('Bank Name', validators=[DataRequired()])
    bank_branch = StringField('Bank Branch', validators=[DataRequired()])

    def populate_from_academic_info(self, academic_info):
        if academic_info:
            self.institution_name.data = academic_info.institution_name
            self.education_level.data = academic_info.education_level
            self.year_of_study.data = str(academic_info.year_of_study)
            self.student_id.data = academic_info.student_id
            self.course.data = academic_info.course
            self.school_account_number.data = academic_info.school_account_number
            self.bank_name.data = academic_info.bank_name
            self.bank_branch.data = academic_info.bank_branch

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
    documents = MultipleFileField('Upload Documents', 
        validators=[
            FileRequired(message='At least one document is required'),
            FileAllowed(['pdf'], 'Only PDF files are allowed!')
        ])