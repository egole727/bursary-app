from flask import jsonify
from app import create_app, db
from app.models import User, Profile, Ward, BursaryProgram, Application

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {
        'db': db,
        'User': User,
        'Profile': Profile,
        'Ward': Ward,
        'BursaryProgram': BursaryProgram,
        'Application': Application
    }

@app.route('/api/test')
def test_api():
    # Get counts
    users = User.query.count()
    wards = Ward.query.count()
    programs = BursaryProgram.query.count()
    
    # Get some sample data
    sample_ward = Ward.query.first()
    sample_program = BursaryProgram.query.first()
    
    return jsonify({
        'status': 'success',
        'data': {
            'counts': {
                'users': users,
                'wards': wards,
                'programs': programs
            },
            'sample_data': {
                'ward': {
                    'name': sample_ward.name,
                    'budget': sample_ward.total_budget
                },
                'program': {
                    'name': sample_program.name,
                    'amount': sample_program.amount,
                    'status': sample_program.status
                }
            }
        }
    })
