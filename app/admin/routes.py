from flask import render_template, redirect, url_for, flash, request, current_app, send_file
from flask_login import login_required, current_user
from app import db
from app.admin import bp
from app.admin.forms import (BursaryProgramForm, WardForm, ApplicationReviewForm, 
                           DocumentForm)
from app.models import (User, BursaryProgram, Ward, Application, 
                       ApplicationTimeline, Document, Profile)
from app.decorators import admin_required
from datetime import datetime
from sqlalchemy import and_, func
import os

@bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    # Get application statistics
    stats = {
        'total_applications': Application.query.count(),
        'pending_applications': Application.query.filter_by(status='PENDING').count(),
        'approved_applications': Application.query.filter_by(status='APPROVED').count(),
        'rejected_applications': Application.query.filter_by(status='REJECTED').count(),
        'active_programs': BursaryProgram.query.filter_by(status='ACTIVE').count(),
        'total_wards': Ward.query.count(),
        'total_budget': db.session.query(func.sum(BursaryProgram.amount)).scalar() or 0,
        'allocated_budget': db.session.query(
            func.sum(Application.amount)
        ).filter(Application.status == 'APPROVED').scalar() or 0
    }
    
    # Get recent applications
    recent_applications = Application.query.order_by(
        Application.created_at.desc()
    ).limit(10).all()

    return render_template('admin/dashboard.html',
                         stats=stats,
                         recent_applications=recent_applications)

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
    form.ward_id.choices = [(w.id, w.name) for w in Ward.query.order_by(Ward.name).all()]
    
    if form.validate_on_submit():
        program = BursaryProgram(
            name=form.name.data,
            description=form.description.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            amount=form.amount.data,
            ward_id=form.ward_id.data
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
    form.ward_id.choices = [(w.id, w.name) for w in Ward.query.order_by(Ward.name).all()]
    
    if form.validate_on_submit():
        program.name = form.name.data
        program.description = form.description.data
        program.start_date = form.start_date.data
        program.end_date = form.end_date.data
        program.amount = form.amount.data
        program.ward_id = form.ward_id.data
        db.session.commit()
        flash('Bursary program has been updated.', 'success')
        return redirect(url_for('admin.programs'))
    
    return render_template('admin/program_form.html', form=form, program=program)

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

@bp.route('/application/<int:application_id>/review', methods=['GET', 'POST'])
@login_required
@admin_required
def review_application(application_id):
    application = Application.query.get_or_404(application_id)
    form = ApplicationReviewForm()
    
    if form.validate_on_submit():
        application.status = form.status.data
        application.review_note = form.comments.data
        application.reviewed_by = current_user.id
        
        timeline = ApplicationTimeline(
            application_id=application.id,
            status=form.status.data,
            comment=form.comments.data
        )
        
        db.session.add(timeline)
        db.session.commit()
        
        flash('Application has been reviewed successfully.', 'success')
        return redirect(url_for('admin.applications'))
    
    return render_template('admin/review_application.html',
                         application=application,
                         form=form)

@bp.route('/document/<int:document_id>/download')
@login_required
@admin_required
def download_document(document_id):
    document = Document.query.get_or_404(document_id)
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], document.url)
    
    if not os.path.exists(file_path):
        flash('Document file not found.', 'error')
        return redirect(url_for('admin.applications'))
        
    try:
        return send_file(
            file_path,
            as_attachment=True,
            download_name=document.url
        )
    except Exception as e:
        flash(f'Error downloading document: {str(e)}', 'error')
        return redirect(url_for('admin.applications'))

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
