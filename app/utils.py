from flask import current_app
import boto3
from botocore.exceptions import ClientError
from werkzeug.utils import secure_filename
import uuid
import os

def upload_file_to_s3(file, bucket):
    try:
        # Validate file
        if not file:
            current_app.logger.error("No file provided")
            return None
            
        # Check file size (5MB limit)
        file.seek(0, os.SEEK_END)
        size = file.tell()
        if size > 5 * 1024 * 1024:
            current_app.logger.error("File too large")
            return None
        file.seek(0)

        # Define allowed file types
        ALLOWED_MIMETYPES = {
            'application/pdf': '.pdf'
        }
        
        # Validate file type
        content_type = file.content_type
        if content_type not in ALLOWED_MIMETYPES:
            current_app.logger.error(f"Invalid file type: {content_type}")
            return None
        
        # Sanitize filename - remove spaces and special characters
        original_filename = secure_filename(file.filename)
        filename_parts = os.path.splitext(original_filename)
        safe_filename = f"{uuid.uuid4()}{filename_parts[1]}"
        
        # Initialize S3 client
        s3_client = boto3.client(
            's3',
            aws_access_key_id=current_app.config['AWS_ACCESS_KEY_ID'],
            aws_secret_access_key=current_app.config['AWS_SECRET_ACCESS_KEY'],
            region_name=current_app.config['AWS_S3_REGION']
        )

        # Upload with explicit content type
        s3_client.upload_fileobj(
            file,
            bucket,
            safe_filename,
            ExtraArgs={'ContentType': content_type}
        )
        
        url = f"https://{bucket}.s3.{current_app.config['AWS_S3_REGION']}.amazonaws.com/{safe_filename}"
        current_app.logger.info(f"File uploaded successfully: {url}")
        return url
        
    except ClientError as e:
        current_app.logger.error(f"AWS S3 error: {str(e)}")
        return None
    except Exception as e:
        current_app.logger.error(f"Unexpected error: {str(e)}")
        return None