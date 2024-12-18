from flask import render_template, redirect, url_for, flash, request, current_app, send_file, jsonify, send_from_directory
from flask_login import login_required, current_user
from app import db
from app.admin import bp
from app.admin.forms import (BursaryProgramForm, WardForm, ApplicationReviewForm, 
                           DocumentForm, WardAdminForm)
from app.models import (User, BursaryProgram, Ward, Application, 
                       ApplicationTimeline, Profile, Document as DocumentModel, AcademicInfo)
from app.decorators import admin_required
from datetime import datetime
from sqlalchemy import and_, func
import os
import io
import csv
from functools import wraps
from datetime import datetime
from docx import Document, document
from docx.shared import Inches
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from flask import send_file
from werkzeug.utils import secure_filename
import pandas as pd
from sqlalchemy import func, case
from datetime import datetime, timedelta


@bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    # Calculate total budget across all wards
    total_budget = db.session.query(func.sum(Ward.total_budget)).scalar() or 0
    
    # Calculate total allocated amount
    allocated_budget = db.session.query(func.sum(Application.amount_allocated))\
        .filter(Application.status == 'APPROVED')\
        .scalar() or 0

    # Organize all statistics into a stats dictionary
    stats = {
        'total_applications': Application.query.count(),
        'pending_applications': Application.query.filter_by(status='PENDING').count(),
        'approved_applications': Application.query.filter_by(status='APPROVED').count(),
        'rejected_applications': Application.query.filter_by(status='REJECTED').count(),
        'allocated_budget': allocated_budget,
        'total_budget': total_budget,
        'budget_remaining': total_budget - allocated_budget
    }
    
    # Get recent applications
    recent_applications = Application.query\
        .order_by(Application.created_at.desc())\
        .limit(5)\
        .all()
    
    # Get ward statistics
    wards = Ward.query.all()
    ward_stats = []
    
    for ward in wards:
        total_ward_allocated = db.session.query(func.sum(Application.amount_allocated))\
            .filter(Application.ward_id == ward.id, 
                   Application.status == 'APPROVED')\
            .scalar() or 0
            
        ward_stats.append({
            'name': ward.name,
            'total_applications': Application.query.filter_by(ward_id=ward.id).count(),
            'allocated_budget': total_ward_allocated,
            'budget_remaining': ward.total_budget - total_ward_allocated
        })

    return render_template('admin/dashboard.html',
                         stats=stats,
                         recent_applications=recent_applications,
                         ward_stats=ward_stats)

@bp.route('/programs')
@login_required
@admin_required
def programs():
    programs = BursaryProgram.query.order_by(BursaryProgram.created_at.desc()).all()
    return render_template('admin/programs.html', programs=programs, now=datetime.now)

@bp.route('/program/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_program():
    form = BursaryProgramForm()
    
    if form.validate_on_submit():
        program = BursaryProgram(
            name=form.name.data,
            description=form.description.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            amount=form.amount.data,
            ward_id=None if form.ward_id.data == -1 else form.ward_id.data
        )
        db.session.add(program)
        db.session.commit()
        flash('New bursary program has been created.', 'success')
        return redirect(url_for('admin.programs'))
    
    return render_template('admin/program_form.html', form=form)

@bp.route('/program/<int:program_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_program(program_id):
    program = BursaryProgram.query.get_or_404(program_id)
    form = BursaryProgramForm(obj=program)
    
    if form.validate_on_submit():
        program.name = form.name.data
        program.description = form.description.data
        program.start_date = form.start_date.data
        program.end_date = form.end_date.data
        program.amount = form.amount.data
        program.ward_id = None if form.ward_id.data == -1 else form.ward_id.data
        db.session.commit()
        flash('Bursary program has been updated.', 'success')
        return redirect(url_for('admin.programs'))
    
    if program.ward_id is None:
        form.ward_id.data = -1
    
    return render_template('admin/program_form.html', form=form, program=program)

@bp.route('/program/<int:program_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_program(program_id):
    program = BursaryProgram.query.get_or_404(program_id)
    
    # Check if there are any applications for this program
    if program.applications.count() > 0:
        flash('Cannot delete program that has applications.', 'error')
        return redirect(url_for('admin.programs'))
    
    try:
        db.session.delete(program)
        db.session.commit()
        flash('Program has been deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting program: {str(e)}', 'error')
    
    return redirect(url_for('admin.programs'))

@bp.route('/applications')
@login_required
@admin_required
def applications():
    status = request.args.get('status')
    program_id = request.args.get('program', type=int)
    ward_id = request.args.get('ward', type=int)
    
    query = Application.query
    
    if status:
        query = query.filter(Application.status == status)
    if program_id:
        query = query.filter(Application.program_id == program_id)
    if ward_id:
        query = query.join(User, Application.student_id == User.id)\
                    .join(Profile)\
                    .filter(Profile.ward_id == ward_id)
    
    applications = query.order_by(Application.created_at.desc()).all()
    programs = BursaryProgram.query.order_by(BursaryProgram.name).all()
    wards = Ward.query.order_by(Ward.name).all()
    
    return render_template('admin/applications.html',
                         applications=applications,
                         programs=programs,
                         wards=wards)

@bp.route('/applications/<int:application_id>/review', methods=['GET', 'POST'])
@login_required
@admin_required
def review_application(application_id):
    # Get the application
    application = Application.query.get_or_404(application_id)
    
    # Create the review form
    form = ApplicationReviewForm()
    
    if form.validate_on_submit():
        # Update application with form data
        application.status = form.status.data
        application.amount_allocated = form.amount_allocated.data
        
        # Add review note to timeline
        timeline_entry = ApplicationTimeline(
            application_id=application.id,
            status=form.status.data,
            comment=form.review_note.data
        )
        db.session.add(timeline_entry)
        
        # Set reviewer
        application.reviewer_id = current_user.id
        application.updated_at = datetime.utcnow()
        
        db.session.commit()
        flash('Application has been reviewed successfully.', 'success')
        return redirect(url_for('admin.applications'))
    
    # Pre-fill form if application is already reviewed
    if application.status != 'PENDING':
        form.status.data = application.status
        form.amount_allocated.data = application.amount_allocated

    # Get documents
    documents = DocumentModel.query.filter_by(application_id=application.id).all()
    return render_template('admin/review_application.html',
                         title='Review Application',
                         form=form,
                         application=application,
                         documents=documents)

@bp.route('/document/<int:doc_id>')
@login_required
@admin_required
def view_document(doc_id):
    """View a specific document"""
    document = DocumentModel.query.get_or_404(doc_id)
    # uploads_dir = current_app.config['UPLOAD_FOLDER']
    return redirect(document.url)

@bp.route('/wards')
@login_required
@admin_required
def wards():
    wards = Ward.query.order_by(Ward.name).all()
    return render_template('admin/wards.html', wards=wards)

@bp.route('/ward/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_ward():
    form = WardForm()
    
    if form.validate_on_submit():
        ward = Ward(
            name=form.name.data,
            description=form.description.data,
            total_budget=form.total_budget.data
        )
        db.session.add(ward)
        db.session.commit()
        flash('New ward has been created.', 'success')
        return redirect(url_for('admin.wards'))
    
    return render_template('admin/ward_form.html', form=form)

@bp.route('/ward/<int:ward_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_ward(ward_id):
    ward = Ward.query.get_or_404(ward_id)
    form = WardForm(obj=ward)
    
    if form.validate_on_submit():
        ward.name = form.name.data
        ward.description = form.description.data
        ward.total_budget = form.total_budget.data
        db.session.commit()
        flash('Ward has been updated.', 'success')
        return redirect(url_for('admin.wards'))
    
    return render_template('admin/ward_form.html', form=form, ward=ward)

@bp.route('/ward/<int:ward_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_ward(ward_id):
    ward = Ward.query.get_or_404(ward_id)
    
    # Check if there are any programs or applications in this ward  
    if ward.programs.count() > 0:
        flash('Cannot delete ward that has active programs.', 'error')
        return redirect(url_for('admin.wards'))
    
    if ward.profiles.count() > 0:
        flash('Cannot delete ward that has registered students.', 'error')
        return redirect(url_for('admin.wards'))
    
    try:
        db.session.delete(ward)
        db.session.commit()
        flash('Ward has been deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting ward: {str(e)}', 'error')
    
    return redirect(url_for('admin.wards'))

@bp.route('/reports')
@login_required
@admin_required
def reports():
    # Summary statistics
    total_applications = Application.query.count()
    pending_applications = Application.query.filter_by(status='PENDING').count()
    approved_applications = Application.query.filter_by(status='APPROVED').count()
    total_amount_approved = db.session.query(func.sum(Application.amount_allocated))\
        .filter_by(status='APPROVED').scalar() or 0

    # Get ward-wise statistics using coalesce to handle NULL values
    ward_stats = db.session.query(
        Ward.id,
        Ward.name,
        func.count(Application.id).label('total_applications'),
        func.coalesce(
            func.sum(
                case(
                    (Application.status == 'APPROVED', Application.amount_allocated),
                    else_=0
                )
            ), 0
        ).label('total_approved')
    ).outerjoin(Application, Ward.id == Application.ward_id)\
     .group_by(Ward.id, Ward.name)\
     .all()

    return render_template('admin/reports.html',
                         total_applications=total_applications,
                         pending_applications=pending_applications,
                         approved_applications=approved_applications,
                         total_amount_approved=total_amount_approved,
                         ward_stats=ward_stats)

@bp.route('/export_report', methods=['GET'])
@login_required
@admin_required
def export_report():
    report_type = request.args.get('type', 'applications')
    format = request.args.get('format', 'excel')
    ward_id = request.args.get('ward_id', None)
    
    # Base query with academic information joined
    query = db.session.query(
        Application,
        User,
        AcademicInfo,
        BursaryProgram,
        Ward
    ).join(
        User, Application.student_id == User.id
    ).join(
        AcademicInfo, User.id == AcademicInfo.user_id
    ).join(
        BursaryProgram, Application.program_id == BursaryProgram.id
    ).join(
        Ward, Application.ward_id == Ward.id
    )

    if ward_id:
        query = query.filter(Application.ward_id == ward_id)

    applications = query.all()
    
    if format == 'excel':
        # Create Excel workbook
        output = io.BytesIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter')
        
        # Prepare data for DataFrame
        data = []
        for app, user, academic_info, program, ward in applications:
            data.append({
                'Application ID': app.id,
                'Student Name': f"{user.first_name} {user.last_name}",
                'Institution': academic_info.institution_name,
                'Admission No': academic_info.student_id,
                'Course': academic_info.course,
                'Year of Study': academic_info.year_of_study,
                'Ward': ward.name,
                'Program': program.name,
                'Amount Requested': app.amount_requested,
                'Amount Allocated': app.amount_allocated or 0,
                'Status': app.status,
                'Application Date': app.created_at.strftime('%Y-%m-%d'),
                'Review Date': app.updated_at.strftime('%Y-%m-%d') if app.updated_at else ''
            })
        
        df = pd.DataFrame(data)
        df.to_excel(writer, sheet_name='Applications', index=False)
        
        # Adjust column widths
        worksheet = writer.sheets['Applications']
        for i, col in enumerate(df.columns):
            column_len = max(df[col].astype(str).apply(len).max(), len(col)) + 2
            worksheet.set_column(i, i, column_len)
        
        writer.close()
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'bursary_applications_report_{datetime.now().strftime("%Y%m%d")}.xlsx'
        )
    
    elif format == 'csv':
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write headers
        writer.writerow([
            'Application ID', 'Student Name', 'Institution', 'Admission No',
            'Course', 'Year of Study', 'Ward', 'Program', 'Amount Requested',
            'Amount Allocated', 'Status', 'Application Date', 'Review Date'
        ])
        
        # Write data
        for app, user, academic_info, program, ward in applications:
            writer.writerow([
                app.id,
                f"{user.first_name} {user.last_name}",
                academic_info.institution_name,
                academic_info.student_id,
                academic_info.course,
                academic_info.year_of_study,
                ward.name,
                program.name,
                app.amount_requested,
                app.amount_allocated or 0,
                app.status,
                app.created_at.strftime('%Y-%m-%d'),
                app.updated_at.strftime('%Y-%m-%d') if app.updated_at else ''
            ])
        
        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'bursary_applications_report_{datetime.now().strftime("%Y%m%d")}.csv'
        )

@bp.route('/reports/ward/<int:ward_id>')
@login_required
@admin_required
def ward_report(ward_id):
    # Get the ward
    ward = Ward.query.get_or_404(ward_id)
    
    # Get all applications for this ward
    applications = Application.query.filter_by(ward_id=ward_id).all()
    
    # Calculate status distribution
    status_counts = {}
    status_amounts = {}
    total_apps = len(applications)
    
    # Initialize the dictionaries first
    for status in ['PENDING', 'APPROVED', 'REJECTED']:
        status_counts[status] = 0
        status_amounts[status] = 0
    
    # Now count and sum
    for app in applications:
        status_counts[app.status] += 1
        if app.status == 'APPROVED':
            status_amounts[app.status] += (app.amount_allocated or 0)
    
    # Create status distribution list
    status_distribution = []
    for status in status_counts:
        if total_apps > 0:
            percentage = (status_counts[status] / total_apps) * 100
        else:
            percentage = 0
            
        status_distribution.append({
            'name': status,
            'count': status_counts[status],
            'percentage': percentage,
            'amount': status_amounts[status]
        })
    
    # Get ward statistics using direct queries
    approved_count = Application.query.filter_by(
        ward_id=ward_id, 
        status='APPROVED'
    ).count()
    
    total_allocated = db.session.query(
        func.coalesce(func.sum(Application.amount_allocated), 0)
    ).filter(
        Application.ward_id == ward_id,
        Application.status == 'APPROVED'
    ).scalar()
    
    # Compile stats
    stats = {
        'total_applications': total_apps,
        'approved_applications': approved_count,
        'total_allocated_amount': total_allocated,
        'total_amount': total_allocated,
        'budget_remaining': ward.total_budget - total_allocated,
        'status_distribution': status_distribution
    }
    
    # Get recent applications
    recent_applications = Application.query\
        .filter_by(ward_id=ward_id)\
        .order_by(Application.created_at.desc())\
        .limit(10)\
        .all()
    
    return render_template('admin/ward_report.html', 
                         ward=ward, 
                         stats=stats, 
                         applications=recent_applications)

@bp.route('/ward-admins')
@login_required
@admin_required
def ward_admins():
    """List all ward admins"""
    ward_admins = User.query.filter_by(role='WARD_ADMIN').all()
    return render_template('admin/ward_admins.html', ward_admins=ward_admins)

@bp.route('/ward-admin/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_ward_admin():
    """Create a new ward admin"""
    form = WardAdminForm()
    
    if form.validate_on_submit():
        try:
            ward_admin = User(
                username=form.username.data,
                email=form.email.data,
                role='WARD_ADMIN',
                ward_id=form.ward_id.data
            )
            ward_admin.set_password(form.password.data)
            
            db.session.add(ward_admin)
            db.session.commit()
            
            flash('Ward admin created successfully!', 'success')
            return redirect(url_for('admin.ward_admins'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating ward admin: {str(e)}', 'error')
            
    return render_template('admin/ward_admin_form.html', form=form, title='New Ward Admin')

@bp.route('/ward-admin/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_ward_admin(id):
    ward_admin = User.query.filter_by(id=id, role='WARD_ADMIN').first_or_404()
    form = WardAdminForm(obj=ward_admin)
    
    if form.validate_on_submit():
        try:
            ward_admin.username = form.username.data
            ward_admin.email = form.email.data
            ward_admin.ward_id = form.ward_id.data
            
            db.session.commit()
            flash('Ward admin updated successfully!', 'success')
            return redirect(url_for('admin.ward_admins'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating ward admin: {str(e)}', 'error')
    
    return render_template('admin/ward_admin_form.html', form=form, ward_admin=ward_admin)

@bp.route('/ward-admin/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_ward_admin(id):
    ward_admin = User.query.filter_by(id=id, role='WARD_ADMIN').first_or_404()
    
    try:
        # Check if ward admin has reviewed any applications
        if ward_admin.reviewed_applications.count() > 0:
            flash('Cannot delete ward admin who has reviewed applications.', 'error')
            return redirect(url_for('admin.ward_admins'))
        
        db.session.delete(ward_admin)
        db.session.commit()
        flash('Ward admin deleted successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting ward admin: {str(e)}', 'error')
    
    return redirect(url_for('admin.ward_admins'))
