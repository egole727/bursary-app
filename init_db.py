from app import create_app, db
from app.models import User, Profile, Ward, BursaryProgram, Application, Document, ApplicationTimeline, AcademicInfo
from datetime import datetime, timedelta

app = create_app()

def init_db():
    with app.app_context():
        # Create all tables
        db.drop_all()  # Drop all tables first to ensure clean state
        db.create_all()
        
        # Check if admin user exists
        admin = User.query.filter_by(email='admin@example.com').first()
        if not admin:
            # Create admin user
            admin = User(
                email='admin@example.com',
                first_name='Admin',
                last_name='User',
                role='ADMIN'
            )
            admin.set_password('admin123')  # Remember to change this in production
            db.session.add(admin)
            
            # Create test wards
            wards = [
                Ward(name='Westlands', total_budget=2000000.0),
                Ward(name='Parklands', total_budget=1800000.0),
                Ward(name='Eastleigh', total_budget=1500000.0),
                Ward(name='Karen', total_budget=2500000.0)
            ]
            for ward in wards:
                db.session.add(ward)
            
            db.session.flush()  # Flush to get ward IDs
            
            # Create test bursary programs
            programs = [
                BursaryProgram(
                    name='Secondary School Bursary 2024',
                    description='Bursary for secondary school students',
                    amount=50000.0,
                    start_date=datetime.now(),
                    end_date=datetime.now() + timedelta(days=30),
                    requirements='Must be a resident of the ward\nMust be enrolled in a secondary school\nFamily income below threshold',
                    status='ACTIVE',
                    ward_id=wards[0].id  # Assign to Westlands ward
                ),
                BursaryProgram(
                    name='University Bursary 2024',
                    description='Bursary for university students',
                    amount=100000.0,
                    start_date=datetime.now(),
                    end_date=datetime.now() + timedelta(days=45),
                    requirements='Must be a resident of the ward\nMust be enrolled in a recognized university\nFamily income below threshold',
                    status='ACTIVE',
                    ward_id=wards[1].id  # Assign to Parklands ward
                )
            ]
            for program in programs:
                db.session.add(program)
            
            # Create a test student user
            student = User(
                email='student@example.com',
                first_name='John',
                last_name='Doe',
                role='STUDENT'
            )
            student.set_password('student123')
            db.session.add(student)
            
            db.session.flush()  # Flush to get student ID
            
            # Create student profile
            profile = Profile(
                user_id=student.id,
                id_number='12345678',
                phone_number='0712345678',
                date_of_birth=datetime(2000, 1, 1),
                gender='Male',
                address='123 Test Street',
                ward_id=wards[0].id  # Assign to Westlands ward
            )
            db.session.add(profile)
            
            # Create academic info for student
            academic_info = AcademicInfo(
                user_id=student.id,
                school_name='Example Secondary School',
                current_grade='Form 4'
            )
            db.session.add(academic_info)
            
            db.session.commit()
            print("Database initialized successfully with:")
            print("- Admin user (email: admin@example.com, password: admin123)")
            print("- Student user (email: student@example.com, password: student123)")
            print("- 4 Wards (Westlands, Parklands, Eastleigh, Karen)")
            print("- 2 Bursary Programs (Secondary School and University)")
        else:
            print("Database already initialized")

if __name__ == '__main__':
    init_db()
