from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager
from sqlalchemy import CheckConstraint

class User(UserMixin, db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    email_verified = db.Column(db.Boolean, default=False)
    email_verification_token = db.Column(db.String(100), unique=True)
    email_verification_sent_at = db.Column(db.DateTime)
    password_hash = db.Column(db.String(256))
    password_reset_token = db.Column(db.String(100), unique=True)
    password_reset_expires = db.Column(db.DateTime)
    first_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))
    username = db.Column(db.String(64), unique=True, nullable=False)
    role = db.Column(db.String(20), default='STUDENT')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    profile = db.relationship('Profile', backref='user', uselist=False)
    submitted_applications = db.relationship('Application', backref='applicant', 
                                          lazy='dynamic', 
                                          foreign_keys='Application.student_id')
    reviewed_applications = db.relationship('Application', backref='reviewer',
                                         lazy='dynamic',
                                         foreign_keys='Application.reviewed_by')
    academic_info = db.relationship('AcademicInfo', backref='user', uselist=False)
    ward_id = db.Column(db.Integer, db.ForeignKey('ward.id'))
    ward = db.relationship('Ward', backref='admins')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_admin(self):
        return self.role == 'ADMIN'
    
    def is_ward_admin(self):
        return self.role == 'WARD_ADMIN'
    
    def is_student(self):
        return self.role == 'STUDENT'

    # helper methods for ward admin functionality
    def can_access_ward(self, ward_id):
        """Check if user has access to a specific ward"""
        if self.role == 'ADMIN':
            return True
        if self.role == 'WARD_ADMIN':
            return self.ward_id == ward_id
        return False

    def get_managed_applications(self):
        """Get applications based on user role"""
        if self.role == 'ADMIN':
            return Application.query.all()
        if self.role == 'WARD_ADMIN':
            return Application.query.filter_by(ward_id=self.ward_id).all()
        return Application.query.filter_by(student_id=self.id).all()

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))

class Profile(db.Model):
    __tablename__ = 'profile'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', name='fk_profile_user'), unique=True)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    phone_number = db.Column(db.String(10), unique=True, nullable=False)
    date_of_birth = db.Column(db.Date)
    gender = db.Column(db.String(10))
    ward_id = db.Column(db.Integer, db.ForeignKey('ward.id', name='fk_profile_ward'))
    id_number = db.Column(db.String(10), unique=True, nullable=False)
    

class Ward(db.Model):
    __tablename__ = 'ward'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(500))
    total_budget = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    programs = db.relationship('BursaryProgram', backref='ward', lazy='dynamic')
    profiles = db.relationship('Profile', backref='ward', lazy='dynamic')
    applications = db.relationship('Application', backref='ward', lazy='dynamic')

class BursaryProgram(db.Model):
    __tablename__ = 'bursary_program'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    amount = db.Column(db.Float, nullable=False)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    requirements = db.Column(db.Text)
    ward_id = db.Column(db.Integer, db.ForeignKey('ward.id'), nullable=True)
    status = db.Column(db.String(20), default='ACTIVE')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    applications = db.relationship('Application', backref='program', lazy='dynamic')

class Application(db.Model):
    __tablename__ = 'application'

    def validate_documents(self):
        if not self.documents.count():
            raise ValueError("At least one document must be uploaded")

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    ward_id = db.Column(db.Integer, db.ForeignKey('ward.id'), nullable=False)
    program_id = db.Column(db.Integer, db.ForeignKey('bursary_program.id'), nullable=False)
    status = db.Column(db.String(50), default='PENDING')
    amount = db.Column(db.Float, nullable=False)
    reason = db.Column(db.Text, nullable=False)
    reviewed_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    review_note = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    documents = db.relationship('Document', backref='application', lazy='dynamic')
    timeline = db.relationship('ApplicationTimeline', backref='application', lazy='dynamic')

class Document(db.Model):
    __tablename__ = 'document'
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), nullable=False)
    url = db.Column(db.String(500), nullable=False)     # original filename
    application_id = db.Column(db.Integer, db.ForeignKey('application.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class AcademicInfo(db.Model):
    __tablename__ = 'academic_info'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Institution Details
    institution_name = db.Column(db.String(255), nullable=False)
    education_level = db.Column(db.String(50), nullable=False)
    year_of_study = db.Column(db.String(20), nullable=False)
    student_id = db.Column(db.String(50), nullable=False)
    course = db.Column(db.String(255), nullable=True)  # Optional for primary/secondary students
    
    # Banking Details
    school_account_number = db.Column(db.String(50), nullable=False)
    bank_name = db.Column(db.String(100), nullable=False)
    bank_branch = db.Column(db.String(100), nullable=False)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<AcademicInfo {self.institution_name}>'

class ApplicationTimeline(db.Model):
    __tablename__ = 'application_timeline'
    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('application.id'), nullable=False)
    status = db.Column(db.String(50), nullable=False)
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
