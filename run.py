from app import create_app
import os
from dotenv import load_dotenv

load_dotenv()

# import secrets

# print("=== Generated Secret Keys ===")
# print(f"SECRET_KEY={secrets.token_hex(32)}")
# print(f"WTF_CSRF_SECRET_KEY={secrets.token_hex(32)}")
# print(f"JWT_SECRET_KEY={secrets.token_hex(32)}")
# print("===========================")

app = create_app()

if __name__ == "__main__":
    # Set environment variables for development
    os.environ['FLASK_ENV'] = 'development'
    os.environ['FLASK_DEBUG'] = '1'
    
    # Run app with debug mode enabled
    app.run(
        host="0.0.0.0",
        debug=True,  # Enables debug mode
        port=int(os.environ.get("PORT", 5000)),
        use_reloader=True  # Enables hot reload
    )
