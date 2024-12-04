import os
import asyncio
from sqlalchemy import text
from dotenv import load_dotenv
from urllib.parse import urlparse
from sqlalchemy.ext.asyncio import create_async_engine
from datetime import timedelta

load_dotenv()

class Config:
    # Database settings
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # File Upload settings
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}

    SECRET_KEY = os.environ.get('SECRET_KEY')
    
    # JWT settings
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)

    # HTTPS/SSL
    SESSION_COOKIE_SECURE = True  # Cookies only sent over HTTPS
    REMEMBER_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    
    # CSRF Protection (you already have this)
    WTF_CSRF_ENABLED = True
    WTF_CSRF_SECRET_KEY = os.environ.get('WTF_CSRF_SECRET_KEY')
    
    # Security Headers
    SECURITY_HEADERS = {
    'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
    # Forces browsers to use HTTPS for 1 year (31536000 seconds)
    
    'X-Content-Type-Options': 'nosniff',
    # Prevents browsers from MIME-sniffing (guessing file types)
    
    'X-Frame-Options': 'SAMEORIGIN',
    # Prevents your site from being embedded in iframes on other sites
    # Protects against clickjacking attacks
    
    'X-XSS-Protection': '1; mode=block'
    # Enables browser's XSS filtering
    # Blocks page if XSS attack is detected
}

# Database connection test
tmpPostgres = urlparse(os.getenv("DATABASE_URL"))

async def async_main() -> None:
    engine = create_async_engine(f"postgresql+asyncpg://{tmpPostgres.username}:{tmpPostgres.password}@{tmpPostgres.hostname}{tmpPostgres.path}?ssl=require", echo=True)
    async with engine.connect() as conn:
        result = await conn.execute(text("select 'hello world'"))
        print(result.fetchall())
    await engine.dispose()

asyncio.run(async_main())
    