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
    
    # JWT settings
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'your-jwt-secret'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)

# Database connection test
tmpPostgres = urlparse(os.getenv("DATABASE_URL"))

async def async_main() -> None:
    engine = create_async_engine(f"postgresql+asyncpg://{tmpPostgres.username}:{tmpPostgres.password}@{tmpPostgres.hostname}{tmpPostgres.path}?ssl=require", echo=True)
    async with engine.connect() as conn:
        result = await conn.execute(text("select 'hello world'"))
        print(result.fetchall())
    await engine.dispose()

asyncio.run(async_main())
    