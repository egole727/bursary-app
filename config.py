import os
import asyncio
from sqlalchemy import text
from dotenv import load_dotenv
from urllib.parse import urlparse
from sqlalchemy.ext.asyncio import create_async_engine
from datetime import timedelta

load_dotenv()


class Config:
    # Environment
    ENV = os.environ.get("FLASK_ENV", "production")
    DEBUG = ENV == "development"
    TESTING = False

    # AWS Configuration
    AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
    AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
    AWS_S3_BUCKET = os.environ.get('AWS_S3_BUCKET')
    AWS_S3_REGION = os.environ.get('AWS_S3_REGION')

    # URL Configuration
    if ENV == "development":
        SERVER_NAME = None
        PREFERRED_URL_SCHEME = "http"
        HOST = "127.0.0.1"
        PORT = 5000
    else:
        SERVER_NAME = None
        PREFERRED_URL_SCHEME = "https"

    @classmethod
    def init_app(cls, app):
        # Verify required configuration
        required_configs = [
            'AWS_ACCESS_KEY_ID',
            'AWS_SECRET_ACCESS_KEY',
            'AWS_S3_BUCKET',
            'DATABASE_URL'
        ]
        
        missing = [key for key in required_configs if not os.environ.get(key)]
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True

    # JWT settings
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)

    # File Upload settings
    # UPLOAD_FOLDER = '/home/u946680789/public_html/uploads'
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5MB max file size
    ALLOWED_EXTENSIONS = {"pdf"}

    # Application Settings
    SECRET_KEY = os.environ.get("SECRET_KEY")

    # Database Configuration
    database_url = os.environ.get("DATABASE_URL")
    if database_url and database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    
    SQLALCHEMY_DATABASE_URI = database_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # HTTPS/SSL
    CSRF_ENABLED = True
    CSRF_SECRET_KEY = os.environ.get("CSRF_SECRET_KEY")

    # Email Configuration
    MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", 587))
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "true").lower() in ["true", "on", "1"]
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER") or os.environ.get(
        "MAIL_USERNAME"
    )

    @classmethod
    def verify_aws_config(cls):
        required = ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY', 'AWS_S3_BUCKET', 'AWS_S3_REGION']
        for key in required:
            if not os.environ.get(key):
                raise ValueError(f"Missing required AWS config: {key}")

    # Security Headers
    SECURITY_HEADERS = {
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
        # Forces browsers to use HTTPS for 1 year (31536000 seconds)
        "X-Content-Type-Options": "nosniff",
        # Prevents browsers from MIME-sniffing (guessing file types)
        "X-Frame-Options": "SAMEORIGIN",
        # Prevents your site from being embedded in iframes on other sites
        # Protects against clickjacking attacks
        "X-XSS-Protection": "1; mode=block",
        # Enables browser's XSS filtering
        # Blocks page if XSS attack is detected
    }

class ProductionConfig(Config):
    ENV = 'production'
    DEBUG = False
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        # Configure production-specific logging
        import logging
        from logging.handlers import RotatingFileHandler
        
        file_handler = RotatingFileHandler('app.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

# Database connection test
tmpPostgres = urlparse(os.getenv("DATABASE_URL"))


async def async_main() -> None:
    engine = create_async_engine(
        f"postgresql+asyncpg://{tmpPostgres.username}:{tmpPostgres.password}@{tmpPostgres.hostname}{tmpPostgres.path}?ssl=require",
        echo=True,
    )
    async with engine.connect() as conn:
        result = await conn.execute(text("select 'hello world'"))
        print(result.fetchall())
    await engine.dispose()


asyncio.run(async_main())
