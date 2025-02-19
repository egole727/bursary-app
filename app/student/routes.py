from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from functools import wraps
from app import db
from app.student import bp
from app.student.forms import ApplicationForm, ProfileForm, AcademicInfoForm
from app.models import (
    BursaryProgram,
    Application,
    Document,
    ApplicationTimeline,
    Profile,
    AcademicInfo,
)
from werkzeug.utils import secure_filename
import logging
from datetime import datetime
import os
import mimetypes
from app.utils import upload_file_to_s3


def student_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != "STUDENT":
            flash("Access denied. This page is only for students.", "error")
            return redirect(url_for("main.index"))
        return f(*args, **kwargs)

    return decorated_function


@bp.route("/dashboard")
@login_required
@student_required
def dashboard():
    # Get user's applications
    applications = (
        Application.query.filter_by(student_id=current_user.id)
        .order_by(Application.created_at.desc())
        .all()
    )

    # Get application statistics
    total_applications = len(applications)
    approved_applications = sum(1 for app in applications if app.status == "APPROVED")
    pending_applications = sum(1 for app in applications if app.status == "PENDING")
    rejected_applications = sum(1 for app in applications if app.status == "REJECTED")

    # Get available bursary programs for student's ward AND programs available to all wards
    current_date = datetime.utcnow()
    available_programs = (
        BursaryProgram.query.filter(
            (
                (BursaryProgram.ward_id == current_user.profile.ward_id)
                | (BursaryProgram.ward_id == None)  # Programs available to all wards
            ),
            BursaryProgram.status == "ACTIVE",
            BursaryProgram.start_date <= current_date,
            BursaryProgram.end_date >= current_date,
        )
        .order_by(BursaryProgram.end_date.asc())
        .all()
    )

    # Get upcoming programs (including those available to all wards)
    upcoming_programs = (
        BursaryProgram.query.filter(
            (
                (BursaryProgram.ward_id == current_user.profile.ward_id)
                | (BursaryProgram.ward_id == None)  # Programs available to all wards
            ),
            BursaryProgram.status == "ACTIVE",
            BursaryProgram.start_date > current_date,
        )
        .order_by(BursaryProgram.start_date.asc())
        .limit(5)
        .all()
    )

    return render_template(
        "student/dashboard.html",
        applications=applications,
        available_programs=available_programs,
        upcoming_programs=upcoming_programs,
        total_applications=total_applications,
        approved_applications=approved_applications,
        pending_applications=pending_applications,
        rejected_applications=rejected_applications,
    )


@bp.route("/profile", methods=["GET", "POST"])
@login_required
@student_required
def profile():
    profile_form = ProfileForm()
    academic_form = AcademicInfoForm()

    # Get existing profile and academic info
    profile = Profile.query.filter_by(user_id=current_user.id).first()
    academic_info = AcademicInfo.query.filter_by(user_id=current_user.id).first()

    if request.method == "GET":
        if profile:
            profile_form.populate_from_profile(profile)
        if academic_info:
            academic_form.populate_from_academic_info(academic_info)

    return render_template(
        "student/profile.html",
        profile_form=profile_form,
        academic_form=academic_form,
        profile=profile,
        academic_info=academic_info,
    )


@bp.route("/update_academic_info", methods=["POST"])
@login_required
@student_required
def update_academic_info():
    form = AcademicInfoForm()
    if form.validate_on_submit():
        academic_info = AcademicInfo.query.filter_by(user_id=current_user.id).first()
        if not academic_info:
            academic_info = AcademicInfo(user_id=current_user.id)

        # Update all fields
        academic_info.institution_name = form.institution_name.data
        academic_info.education_level = form.education_level.data
        academic_info.year_of_study = form.year_of_study.data
        academic_info.student_id = form.student_id.data
        academic_info.course = form.course.data
        academic_info.school_account_number = form.school_account_number.data
        academic_info.bank_name = form.bank_name.data
        academic_info.bank_branch = form.bank_branch.data

        db.session.add(academic_info)
        db.session.commit()

        flash("Academic information updated successfully!", "success")
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{getattr(form, field).label.text}: {error}", "error")

    return redirect(url_for("student.dashboard"))


def allowed_file(filename):
    """Check if the file is a PDF."""
    # Check file extension
    allowed_extensions = {"pdf"}
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_extensions


def validate_file(file):
    """Validate file type and size."""
    # Check if file exists
    if not file or file.filename == "":
        return False, "No file selected"

    # Check file extension
    if not allowed_file(file.filename):
        return False, "Only PDF files are allowed"

    # Check MIME type
    mime_type = mimetypes.guess_type(file.filename)[0]
    if mime_type != "application/pdf":
        return False, "Invalid file type. Only PDF files are allowed"

    # Check file size (5MB limit)
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    if size > 5 * 1024 * 1024:  # 5MB in bytes
        return False, "File size exceeds 5MB limit"

    return True, "File is valid"


import logging

@bp.route("/apply/<int:program_id>", methods=["GET", "POST"])
@login_required
@student_required
def apply(program_id):
    # Check if student has completed their profile
    profile = Profile.query.filter_by(user_id=current_user.id).first()
    if not profile:
        flash(
            "Please complete your profile and academic information before applying for bursaries.",
            "warning",
        )
        return redirect(url_for("student.profile"))

    program = BursaryProgram.query.get_or_404(program_id)

    # Check if program is still accepting applications
    if program.status != "ACTIVE" or program.end_date < datetime.utcnow():
        flash("This program is no longer accepting applications", "error")
        return redirect(url_for("student.dashboard"))

    # Check if student has already applied
    existing_application = Application.query.filter_by(
        student_id=current_user.id, program_id=program_id
    ).first()

    if existing_application:
        flash("You have already applied to this program", "error")
        return redirect(url_for("student.dashboard"))

    form = ApplicationForm()
    if form.validate_on_submit():
        try:
            # Get the student's ward_id from their profile
            student_ward_id = profile.ward_id

            if not student_ward_id:
                flash(
                    "Unable to determine your ward. Please update your profile.",
                    "error",
                )
                return redirect(url_for("student.profile"))

            application = Application(
                student_id=current_user.id,
                program_id=program_id,
                ward_id=student_ward_id,
                amount_requested=form.amount_requested.data,
                reason=form.reason.data,
                status="PENDING",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )

            db.session.add(application)
            db.session.flush()  # Get the application ID

            # Validate documents
            if not form.documents.data or not any(
                file.filename for file in form.documents.data
            ):
                flash("At least one document must be uploaded", "error")
                return redirect(request.url)

            # Handle document uploads
            for file in form.documents.data:
                # Validate each file
                is_valid, message = validate_file(file)
                if not is_valid:
                    flash(
                        f"File validation error ({file.filename}): {message}", "error"
                    )
                    return redirect(request.url)

                # Upload file to S3
                file_url = upload_file_to_s3(file, current_app.config["AWS_S3_BUCKET"])

                if not file_url:
                    flash(f"Failed to upload {file.filename} to S3", "error")
                    return redirect(request.url)

                # Create Document entry with the S3 URL
                document = Document(
                    application_id=application.id,
                    type="SUPPORTING_DOCUMENT",
                    url=file_url,  # Store the S3 URL
                )
                db.session.add(document)

            # Create timeline entry
            timeline = ApplicationTimeline(
                application_id=application.id,
                status="APPLICATION_SUBMITTED",
                comment="Application submitted for review",
                created_at=datetime.utcnow(),
            )

            db.session.add(timeline)
            db.session.commit()

            flash("Your application has been submitted successfully!", "success")
            return redirect(
                url_for("student.view_application", application_id=application.id)
            )

        except Exception as e:
            db.session.rollback()
            flash(f"Error submitting application: {str(e)}", "error")
            logging.error(f"Error submitting application: {str(e)}")

    return render_template("student/apply.html", form=form, program=program)


@bp.route("/application/<int:application_id>")
@login_required
@student_required
def view_application(application_id):
    application = Application.query.get_or_404(application_id)

    # Check if the application belongs to the current user
    if application.student_id != current_user.id:
        flash("You do not have permission to view this application.", "error")
        return redirect(url_for("student.dashboard"))

    return render_template("student/application_details.html", application=application)


@bp.route("/applications")
@login_required
@student_required
def applications():
    """View all applications for the current student."""
    student_applications = (
        Application.query.filter_by(student_id=current_user.id)
        .order_by(Application.created_at.desc())
        .all()
    )
    return render_template(
        "student/applications.html", applications=student_applications
    )


@bp.route("/programs")
@login_required
@student_required
def programs():
    # Get current datetime for comparison
    current_date = datetime.utcnow()

    # Get available bursary programs for student's ward AND programs available to all wards
    available_programs = (
        BursaryProgram.query.filter(
            (
                (BursaryProgram.ward_id == current_user.profile.ward_id)
                | (BursaryProgram.ward_id == None)  # Programs available to all wards
            ),
            BursaryProgram.status == "ACTIVE",
            BursaryProgram.start_date <= current_date,
            BursaryProgram.end_date >= current_date,
        )
        .order_by(BursaryProgram.end_date.asc())
        .all()
    )

    # Get upcoming programs (including those available to all wards)
    upcoming_programs = (
        BursaryProgram.query.filter(
            (
                (BursaryProgram.ward_id == current_user.profile.ward_id)
                | (BursaryProgram.ward_id == None)  # Programs available to all wards
            ),
            BursaryProgram.status == "ACTIVE",
            BursaryProgram.start_date > current_date,
        )
        .order_by(BursaryProgram.start_date.asc())
        .all()
    )

    return render_template(
        "student/programs.html",
        available_programs=available_programs,
        upcoming_programs=upcoming_programs,
    )


@bp.route("/program/<int:id>")
@login_required
@student_required
def program_detail(id):
    """View details of a specific bursary program."""
    from datetime import datetime

    program = BursaryProgram.query.get_or_404(id)

    # Check if program belongs to student's ward
    if program.ward_id != current_user.profile.ward_id:
        flash("You do not have access to this program.", "danger")
        return redirect(url_for("student.programs"))

    # Check if student has already applied
    existing_application = Application.query.filter_by(
        student_id=current_user.id, program_id=program.id
    ).first()

    return render_template(
        "student/program_detail.html",
        program=program,
        has_applied=existing_application is not None,
        now=datetime.now(),
    )


@bp.route("/upload", methods=["POST"])
@student_required
@login_required
def upload():
    if "file" not in request.files:
        flash("No file part")
        return redirect(request.url)
    file = request.files["file"]
    if file.filename == "":
        flash("No selected file")
        return redirect(request.url)
    if file:
        file_url = upload_file_to_s3(file, current_app.config["AWS_S3_BUCKET"])
        if file_url:
            # Save the file URL to the database
            new_document = DocumentModel(url=file_url)
            db.session.add(new_document)
            db.session.commit()
            flash("File uploaded successfully")
        else:
            flash("File upload failed")
    return redirect(url_for("student.dashboard"))
