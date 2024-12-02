from app import create_app, db
from app.models import User

app = create_app()

def test_connection():
    with app.app_context():
        try:
            # Try to query the database
            users = User.query.all()
            print("Database connection successful!")
            print(f"Found {len(users)} users")
        except Exception as e:
            print(f"Error connecting to database: {e}")

if __name__ == "__main__":
    test_connection()
