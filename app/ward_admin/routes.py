from flask import render_template, redirect, url_for, flash, request, send_from_directory, current_app, send_file
from flask_login import login_required, current_user
from app import db
from app.ward_admin import bp
from app.models import Application, User, Ward, BursaryProgram, ApplicationTimeline, Document, AcademicInfo
from app.decorators import ward_admin_required
from app.admin.forms import ApplicationReviewForm
import os
import csv
import io
import pandas as pd
from datetime import datetime
from sqlalchemy.sql import func

@bp.route('/dashboard')
@login_required
@ward_admin_required
def dashboard():
    """Ward Admin Dashboard"""
    # Get statistics for the ward admin's ward
    stats = {
        'total_applications': Application.query.filter_by(ward_id=current_user.ward_id).count(),
        'pending_applications': Application.query.filter_by(
            ward_id=current_user.ward_id, 
            status='PENDING'
        ).count(),
        'approved_applications': Application.query.filter_by(
            ward_id=current_user.ward_id, 
            status='APPROVED'
        ).count(),
        'total_allocated': db.session.query(func.sum(Application.amount_allocated))\
            .filter_by(ward_id=current_user.ward_id, status='APPROVED')\
            .scalar() or 0
    }
    
    # Get recent applications from their ward
    recent_applications = Application.query\
        .filter_by(ward_id=current_user.ward_id)\
        .order_by(Application.created_at.desc())\
        .limit(10)\
        .all()
    
    return render_template('ward_admin/dashboard.html', 
                         stats=stats, 
                         recent_applications=recent_applications)

@bp.route('/applications')
@login_required
@ward_admin_required
def applications():
    """List all applications in the ward admin's ward"""
    applications = Application.query\
        .filter_by(ward_id=current_user.ward_id)\
        .order_by(Application.created_at.desc())\
        .all()
    return render_template('ward_admin/applications.html', applications=applications)

@bp.route('/applications/<int:application_id>/review', methods=['GET', 'POST'])
@login_required
@ward_admin_required
def review_application(application_id):
    application = Application.query.get_or_404(application_id)
    form = ApplicationReviewForm()

    if form.validate_on_submit():
        try:
            # Validate allocation amount
            application.validate_allocation(form.amount_allocated.data)
            
            # Update application
            application.amount_allocated = form.amount_allocated.data
            application.status = form.status.data
            application.review_note = form.review_note.data
            application.reviewed_by = current_user.id
            application.updated_at = datetime.utcnow()

            # Create timeline entry
            timeline_entry = ApplicationTimeline(
                application_id=application.id,
                status=form.status.data,
                comment=f"Amount allocated: KES {form.amount_allocated.data:,.2f}\n{form.review_note.data if form.review_note.data else ''}"
            )
            
            db.session.add(timeline_entry)
            db.session.commit()
            
            flash(f'Application has been {form.status.data.lower()}.', 'success')
            
        except ValueError as e:
            flash(str(e), 'error')
            return redirect(url_for('ward_admin.review_application', application_id=application.id))
        
        except Exception as e:
            db.session.rollback()
            flash('An error occurred while processing the review.', 'error')
            return redirect(url_for('ward_admin.review_application', application_id=application.id))

        return redirect(url_for('ward_admin.applications'))

    # Get documents for this application
    documents = Document.query.filter_by(application_id=application.id).all()
    
    return render_template('ward_admin/review_application.html', 
                         form=form, 
                         application=application,
                         documents=documents)

@bp.route('/document/<int:doc_id>')
@login_required
@ward_admin_required
def view_document(doc_id):
    """View a specific document"""
    document = Document.query.get_or_404(doc_id)
    # Verify the document belongs to an application in the ward admin's ward
    if document.application.ward_id != current_user.ward_id:
        flash('You do not have permission to view this document.', 'error')
        return redirect(url_for('ward_admin.applications'))
    
    uploads_dir = current_app.config['UPLOAD_FOLDER']
    return send_from_directory(uploads_dir, document.url)

@bp.route('/reports')
@login_required
@ward_admin_required
def reports():
    """Generate reports for the ward"""
    ward = Ward.query.get(current_user.ward_id)
    
    # Get ward statistics with rejected applications count
    stats = {
        'total_applications': Application.query.filter_by(ward_id=current_user.ward_id).count(),
        'approved_applications': Application.query.filter_by(
            ward_id=current_user.ward_id, 
            status='APPROVED'
        ).count(),
        'rejected_applications': Application.query.filter_by(
            ward_id=current_user.ward_id, 
            status='REJECTED'
        ).count(),
        'pending_applications': Application.query.filter_by(
            ward_id=current_user.ward_id, 
            status='PENDING'
        ).count(),
        'total_allocated': db.session.query(db.func.sum(Application.amount_allocated))\
            .filter_by(ward_id=current_user.ward_id, status='APPROVED')\
            .scalar() or 0,
        'budget_remaining': ward.total_budget - (
            db.session.query(db.func.sum(Application.amount_allocated))
            .filter_by(ward_id=current_user.ward_id, status='APPROVED')
            .scalar() or 0
        )
    }
    
    return render_template('ward_admin/reports.html', stats=stats, ward=ward)

@bp.route('/reports/export/<format>')
@login_required
@ward_admin_required
def export_reports(format):
    """Export ward reports in CSV or Excel format"""
    # Get all approved applications for the ward
    applications = Application.query.filter_by(
        ward_id=current_user.ward_id,
        status='APPROVED'
    ).all()
    
    # Prepare data for export
    data = []
    for app in applications:
        data.append({
            'Application ID': app.id,
            'Student Name': f"{app.applicant.first_name} {app.applicant.last_name}",
            'Institution': app.applicant.academic_info.institution_name,
            'Admission No': app.applicant.academic_info.student_id,
            'Course': app.applicant.academic_info.course,
            'Year of Study': app.applicant.academic_info.year_of_study,
            'Program': app.program.name,
            'Amount Requested': app.amount_requested,
            'Amount Allocated': app.amount_allocated or 0,
            'Status': app.status,
            'Application Date': app.created_at.strftime('%Y-%m-%d'),
            'Review Date': app.updated_at.strftime('%Y-%m-%d') if app.updated_at else ''
        })
    
    if format == 'csv':
        # Create CSV in memory
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=data[0].keys() if data else [])
        writer.writeheader()
        writer.writerows(data)
        
        # Create the response
        mem_file = io.BytesIO()
        mem_file.write(output.getvalue().encode('utf-8'))
        mem_file.seek(0)
        output.close()
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return send_file(
            mem_file,
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'ward_beneficiaries_{timestamp}.csv'
        )
        
    elif format == 'excel':
        # Create Excel file in memory
        df = pd.DataFrame(data)
        excel_file = io.BytesIO()
        
        # Create Excel writer object
        with pd.ExcelWriter(excel_file, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Beneficiaries', index=False)
            
            # Get workbook and worksheet objects
            workbook = writer.book
            worksheet = writer.sheets['Beneficiaries']
            
            # Add some formatting
            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#4B88B4',
                'font_color': 'white'
            })
            
            # Format the header row
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)
                
            # Adjust column widths
            for i, col in enumerate(df.columns):
                max_length = max(df[col].astype(str).apply(len).max(), len(col)) + 2
                worksheet.set_column(i, i, max_length)
        
        excel_file.seek(0)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return send_file(
            excel_file,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'ward_beneficiaries_{timestamp}.xlsx'
        )
    
    flash('Invalid export format specified.', 'error')
    return redirect(url_for('ward_admin.reports')) 

@bp.route('/reports/export_all', methods=['GET'])
@login_required
@ward_admin_required
def export_report():
    format = request.args.get('format', 'excel')
    
    # Query applications for this ward with academic information
    query = db.session.query(
        Application,
        User,
        AcademicInfo,
        BursaryProgram
    ).join(
        User, Application.student_id == User.id
    ).join(
        AcademicInfo, User.id == AcademicInfo.user_id
    ).join(
        BursaryProgram, Application.program_id == BursaryProgram.id
    ).filter(
        Application.ward_id == current_user.ward_id
    )

    applications = query.all()
    
    if format == 'excel':
        output = io.BytesIO()
        writer = pd.ExcelWriter(output, engine='xlsxwriter')
        
        data = []
        for app, user, academic_info, program in applications:
            data.append({
                'Application ID': app.id,
                'Student Name': f"{user.first_name} {user.last_name}",
                'Institution': academic_info.institution_name,
                'Admission No': academic_info.student_id,
                'Course': academic_info.course,
                'Year of Study': academic_info.year_of_study,
                'Program': program.name,
                'Amount Requested': app.amount_requested,
                'Amount Allocated': app.amount_allocated or 0,
                'Status': app.status,
                'Application Date': app.created_at.strftime('%Y-%m-%d'),
                'Review Date': app.updated_at.strftime('%Y-%m-%d') if app.updated_at else ''
            })
        
        df = pd.DataFrame(data)
        df.to_excel(writer, sheet_name='Applications', index=False)
        
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
            download_name=f'ward_{current_user.ward_id}_applications_{datetime.now().strftime("%Y%m%d")}.xlsx'
        )