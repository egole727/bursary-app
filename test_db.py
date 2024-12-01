from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config
import sys

def test_connection():
    try:
        app = Flask(__name__)
        app.config.from_object(Config)
        db = SQLAlchemy(app)
        
        # Test the connection by executing a simple query
        with app.app_context():
            result = db.session.execute(db.text('SELECT 1')).scalar()
            print("Database connection successful!")
            print(f"Test query result: {result}")
            return True
    except Exception as e:
        print("Error connecting to database:", str(e), file=sys.stderr)
        return False

if __name__ == '__main__':
    success = test_connection()
    sys.exit(0 if success else 1)
