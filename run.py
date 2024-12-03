from app import create_app
import os
# import secrets

# print("=== Generated Secret Keys ===")
# print(f"SECRET_KEY={secrets.token_hex(32)}")
# print(f"WTF_CSRF_SECRET_KEY={secrets.token_hex(32)}")
# print(f"JWT_SECRET_KEY={secrets.token_hex(32)}")
# print("===========================")

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))