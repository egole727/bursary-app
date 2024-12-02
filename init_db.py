from app import create_app, db
from app.models import User, Profile, Ward, BursaryProgram, Application, Document, ApplicationTimeline, AcademicInfo
from datetime import datetime, timedelta

app = create_app()

def init_db():
    with app.app_context():
        # Drop all tables and recreate them
        db.drop_all()
        db.create_all()
        
        # Create an admin user
        admin = User(
            email='admin@example.com',
            first_name='Admin',
            last_name='User',
            role='ADMIN'
        )
        admin.set_password('admin123')
        db.session.add(admin)

        # Create a student user
        student = User(
            email='student@example.com',
            first_name='John',
            last_name='Doe',
            role='STUDENT'
        )
        student.set_password('student123')
        db.session.add(student)
        
        db.session.flush()  # Flush to get user IDs

        # Create wards with descriptions (matching WardForm)
        wards = [
            Ward(
                name='Westlands',
                description='Westlands Sub-County Ward',
                total_budget=2000000.0
            ),
            Ward(
                name='Parklands',
                description='Parklands/Highridge Ward',
                total_budget=1800000.0
            ),
            Ward(
                name='Eastleigh',
                description='Eastleigh North Ward',
                total_budget=1500000.0
            ),
            Ward(
                name='Karen',
                description='Karen/Langata Ward',
                total_budget=2500000.0
            )
        ]
        for ward in wards:
            db.session.add(ward)
        
        db.session.flush()

        # Create student profile (matching ProfileForm)
        profile = Profile(
            user_id=student.id,
            first_name='John',
            last_name='Doe',
            date_of_birth=datetime(2000, 1, 1),
            gender='M',
            phone_number='0712345678',
            ward_id=wards[0].id
        )
        db.session.add(profile)

        # Create academic info (matching AcademicInfoForm)
        academic_info = AcademicInfo(
            user_id=student.id,
            institution='University of Nairobi',
            course='Computer Science',
            year_of_study=2,
            student_id='CS/001/2023'
        )
        db.session.add(academic_info)

        # Create bursary programs (matching BursaryProgramForm)
        programs = [
            BursaryProgram(
                name='Secondary School Bursary 2024',
                description='Financial support for secondary school students',
                amount=50000.0,
                start_date=datetime.now(),
                end_date=datetime.now() + timedelta(days=30),
                requirements='1. Must be a resident of the ward\n2. Must be enrolled in secondary school\n3. Must demonstrate financial need',
                status='ACTIVE',
                ward_id=wards[0].id
            ),
            BursaryProgram(
                name='University Bursary 2024',
                description='Financial support for university students',
                amount=100000.0,
                start_date=datetime.now(),
                end_date=datetime.now() + timedelta(days=45),
                requirements='1. Must be a resident of the ward\n2. Must be enrolled in a recognized university\n3. Must demonstrate financial need',
                status='ACTIVE',
                ward_id=wards[1].id
            )
        ]
        for program in programs:
            db.session.add(program)

        # Create a sample application (matching ApplicationForm)
        application = Application(
            student_id=student.id,
            ward_id=wards[0].id,
            program_id=1,  # First program
            status='PENDING',
            amount=45000.0,
            reason='Need financial assistance to continue my education due to family circumstances.',
            created_at=datetime.utcnow()
        )
        db.session.add(application)

        # Add application timeline entry
        timeline = ApplicationTimeline(
            application_id=1,
            status='PENDING',
            comment='Application submitted',
            created_at=datetime.utcnow()
        )
        db.session.add(timeline)

        db.session.commit()
        
        print("Database initialized successfully with:")
        print("- Admin user (email: admin@example.com, password: admin123)")
        print("- Student user (email: student@example.com, password: student123)")
        print("- 4 Wards (Westlands, Parklands, Eastleigh, Karen)")
        print("- 2 Bursary Programs (Secondary School and University)")
        print("- 1 Sample Application with Timeline")
        print("- Complete Profile and Academic Info for student")

if __name__ == '__main__':
    init_db()