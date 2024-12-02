from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from functools import wraps
from app import db
from app.student import bp
from app.student.forms import ApplicationForm, ProfileForm, AcademicInfoForm
from app.models import BursaryProgram, Application, Document, ApplicationTimeline, Profile, AcademicInfo
from werkzeug.utils import secure_filename
from datetime import datetime
import os

def student_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'STUDENT':
            flash('Access denied. This page is only for students.', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/dashboard')
@login_required
@student_required
def dashboard():
    # Get user's applications
    applications = Application.query.filter_by(student_id=current_user.id).order_by(Application.created_at.desc()).all()
    
    # Get application statistics
    total_applications = len(applications)
    approved_applications = sum(1 for app in applications if app.status == 'APPROVED')
    pending_applications = sum(1 for app in applications if app.status == 'PENDING')
    rejected_applications = sum(1 for app in applications if app.status == 'REJECTED')
    
    # Get available bursary programs for student's ward
    current_date = datetime.utcnow()
    available_programs = BursaryProgram.query.filter(
        BursaryProgram.ward_id == current_user.profile.ward_id,
        BursaryProgram.status == 'ACTIVE',
        BursaryProgram.start_date <= current_date,
        BursaryProgram.end_date >= current_date
    ).order_by(BursaryProgram.end_date.asc()).all()
    
    # Get upcoming programs
    upcoming_programs = BursaryProgram.query.filter(
        BursaryProgram.ward_id == current_user.profile.ward_id,
        BursaryProgram.status == 'ACTIVE',
        BursaryProgram.start_date > current_date
    ).order_by(BursaryProgram.start_date.asc()).limit(5).all()
    
    return render_template('student/dashboard.html',
                         applications=applications,
                         available_programs=available_programs,
                         upcoming_programs=upcoming_programs,
                         total_applications=total_applications,
                         approved_applications=approved_applications,
                         pending_applications=pending_applications,
                         rejected_applications=rejected_applications)

@bp.route('/profile', methods=['GET', 'POST'])
@login_required
@student_required
def profile():
    profile_form = ProfileForm(obj=current_user.profile)
    academic_form = AcademicInfoForm(obj=current_user.academic_info)
    
    if request.method == 'POST':
        if 'submit_profile' in request.form and profile_form.validate_on_submit():
            try:
                if current_user.profile is None:
                    profile = Profile(user_id=current_user.id)
                    db.session.add(profile)
                    current_user.profile = profile
                
                current_user.profile.first_name = profile_form.first_name.data
                current_user.profile.last_name = profile_form.last_name.data
                current_user.profile.date_of_birth = profile_form.date_of_birth.data
                current_user.profile.gender = profile_form.gender.data
                current_user.profile.phone_number = profile_form.phone_number.data
                current_user.profile.ward_id = profile_form.ward_id.data
                
                db.session.commit()
                flash('Profile updated successfully', 'success')
                return redirect(url_for('student.profile'))
            except Exception as e:
                db.session.rollback()
                flash('An error occurred while updating your profile. Please try again.', 'error')
                print(f"Error updating profile: {str(e)}")
        
        if 'submit_academic' in request.form and academic_form.validate_on_submit():
            try:
                if current_user.academic_info is None:
                    academic_info = AcademicInfo(user_id=current_user.id)
                    db.session.add(academic_info)
                    current_user.academic_info = academic_info
                
                current_user.academic_info.institution = academic_form.institution.data
                current_user.academic_info.course = academic_form.course.data
                current_user.academic_info.year_of_study = academic_form.year_of_study.data
                current_user.academic_info.student_id = academic_form.student_id.data
                
                db.session.commit()
                flash('Academic information updated successfully', 'success')
                return redirect(url_for('student.profile'))
            except Exception as e:
                db.session.rollback()
                flash('An error occurred while updating your academic information. Please try again.', 'error')
                print(f"Error updating academic info: {str(e)}")
    
    return render_template('student/profile.html',
                         profile_form=profile_form,
                         academic_form=academic_form)

@bp.route('/apply/<int:program_id>', methods=['GET', 'POST'])
@login_required
@student_required
def apply(program_id):
    # Check if student has completed their profile
    if not current_user.profile or not current_user.academic_info:
        flash('Please complete your profile before applying for bursaries.', 'warning')
        return redirect(url_for('student.profile'))

    program = BursaryProgram.query.get_or_404(program_id)
    
    # Check if program is still accepting applications
    if program.status != 'ACTIVE' or program.end_date < datetime.utcnow():
        flash('This program is no longer accepting applications', 'error')
        return redirect(url_for('student.dashboard'))
    
    # Check if student has already applied
    existing_application = Application.query.filter_by(
        student_id=current_user.id,
        program_id=program_id
    ).first()
    
    if existing_application:
        flash('You have already applied to this program', 'error')
        return redirect(url_for('student.dashboard'))
    
    form = ApplicationForm()
    if form.validate_on_submit():
        try:
            # Create uploads directory if it doesn't exist
            upload_folder = current_app.config['UPLOAD_FOLDER']
            os.makedirs(upload_folder, exist_ok=True)
            
            application = Application(
                student_id=current_user.id,
                program_id=program_id,
                ward_id=program.ward_id,
                amount=form.amount.data,
                reason=form.reason.data,
                status='PENDING'
            )
            
            # Handle document uploads
            uploaded_files = request.files.getlist('documents')
            for file in uploaded_files:
                if file and allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    filepath = os.path.join(upload_folder, filename)
                    file.save(filepath)
                    
                    document = Document(
                        type='SUPPORTING_DOCUMENT',
                        url=filename,
                        application=application
                    )
                    db.session.add(document)
            
            # Create timeline entry
            timeline = ApplicationTimeline(
                application=application,
                status='APPLICATION_SUBMITTED',
                comment='Application submitted for review'
            )
            
            db.session.add(application)
            db.session.add(timeline)
            db.session.commit()
            
            flash('Your application has been submitted successfully!', 'success')
            return redirect(url_for('student.view_application', application_id=application.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error submitting application: {str(e)}', 'error')
            print(f"Error submitting application: {str(e)}")
    
    return render_template('student/apply.html', form=form, program=program)

@bp.route('/application/<int:application_id>')
@login_required
@student_required
def view_application(application_id):
    application = Application.query.get_or_404(application_id)
    
    # Check if the application belongs to the current user
    if application.student_id != current_user.id:
        flash('You do not have permission to view this application.', 'error')
        return redirect(url_for('student.dashboard'))
    
    return render_template('student/application_details.html', application=application)

@bp.route('/applications')
@login_required
@student_required
def applications():
    """View all applications for the current student."""
    student_applications = Application.query.filter_by(student_id=current_user.id).order_by(Application.created_at.desc()).all()
    return render_template('student/applications.html', applications=student_applications)

@bp.route('/programs')
@login_required
@student_required
def programs():
    """View all available and upcoming bursary programs."""
    today = datetime.utcnow()
    
    # Get available programs (current date is between start_date and end_date)
    available_programs = BursaryProgram.query.filter(
        BursaryProgram.start_date <= today,
        BursaryProgram.end_date >= today,
        BursaryProgram.ward_id == current_user.profile.ward_id,
        BursaryProgram.status == 'ACTIVE'
    ).order_by(BursaryProgram.end_date.asc()).all()
    
    # Get upcoming programs (start_date is in the future)
    upcoming_programs = BursaryProgram.query.filter(
        BursaryProgram.start_date > today,
        BursaryProgram.ward_id == current_user.profile.ward_id,
        BursaryProgram.status == 'ACTIVE'
    ).order_by(BursaryProgram.start_date.asc()).all()
    
    return render_template('student/programs.html', 
                         available_programs=available_programs,
                         upcoming_programs=upcoming_programs)

@bp.route('/program/<int:id>')
@login_required
@student_required
def program_detail(id):
    """View details of a specific bursary program."""
    from datetime import datetime
    
    program = BursaryProgram.query.get_or_404(id)
    
    # Check if program belongs to student's ward
    if program.ward_id != current_user.profile.ward_id:
        flash('You do not have access to this program.', 'danger')
        return redirect(url_for('student.programs'))
    
    # Check if student has already applied
    existing_application = Application.query.filter_by(
        student_id=current_user.id,
        program_id=program.id
    ).first()
    
    return render_template('student/program_detail.html', 
                         program=program,
                         has_applied=existing_application is not None,
                         now=datetime.now())

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'doc', 'docx'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# @bp.route('/settings')
# @login_required
# def settings():
#     return render_template('student/settings.html', 
#                          user=current_user,
#                          title='Settings')
