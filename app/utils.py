from flask import current_app
import boto3
from botocore.exceptions import ClientError
from werkzeug.utils import secure_filename
import uuid
import os

def upload_file_to_s3(file, bucket):
    try:
        # Input validation
        if not file:
            current_app.logger.error("File object is None")
            return None
            
        if not hasattr(file, 'filename'):
            current_app.logger.error("Invalid file object - no filename")
            return None
            
        # Debug logging
        current_app.logger.info(f"Uploading file: {file.filename}")
        current_app.logger.info(f"Content type: {getattr(file, 'content_type', 'unknown')}")
        current_app.logger.info(f"File size: {file.content_length if hasattr(file, 'content_length') else 'unknown'}")
        
        # Reset file pointer and check content
        file.seek(0)
        if file.read() == b'':
            current_app.logger.error("File is empty")
            return None
        file.seek(0)
        
        # Generate safe filename
        safe_filename = f"{uuid.uuid4()}-{secure_filename(file.filename)}"
        
        # Initialize S3 client
        s3_client = boto3.client(
            's3',
            aws_access_key_id=current_app.config.get('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=current_app.config.get('AWS_SECRET_ACCESS_KEY'),
            region_name=current_app.config.get('AWS_S3_REGION')
        )
        
        # Upload file
        s3_client.upload_fileobj(
            file,
            bucket,
            safe_filename,
            ExtraArgs={'ContentType': file.content_type or 'application/pdf'}
        )
        
        url = f"https://{bucket}.s3.{current_app.config['AWS_S3_REGION']}.amazonaws.com/{safe_filename}"
        current_app.logger.info(f"Successfully uploaded to: {url}")
        return url
        
    except AttributeError as e:
        current_app.logger.error(f"File object error: {str(e)}")
        return None
    except ClientError as e:
        current_app.logger.error(f"AWS S3 error: {str(e)}")
        return None
    except Exception as e:
        current_app.logger.error(f"Unexpected error: {str(e)}")
        return None