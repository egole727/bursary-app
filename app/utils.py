import boto3
from botocore.exceptions import ClientError
from flask import current_app
from werkzeug.utils import secure_filename
import uuid
import logging

def upload_file_to_s3(file, bucket):
    if not file:
        current_app.logger.error("No file provided")
        return None
        
    try:
        # Initialize S3 client with explicit credentials
        s3_client = boto3.client(
            's3',
            aws_access_key_id=current_app.config['AWS_ACCESS_KEY_ID'],
            aws_secret_access_key=current_app.config['AWS_SECRET_ACCESS_KEY'],
            region_name=current_app.config['AWS_S3_REGION']
        )
        
        # Generate unique filename
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}-{filename}"
        
        # Debug logging
        current_app.logger.info(f"Attempting to upload {filename} to bucket {bucket}")
        current_app.logger.debug(f"AWS Config - Bucket: {bucket}, Region: {current_app.config['AWS_S3_REGION']}")
        
        # Upload file
        s3_client.upload_fileobj(
            file,
            bucket,
            unique_filename,
            ExtraArgs={
                'ContentType': file.content_type,
                'ACL': 'public-read'
            }
        )
        
        # Generate URL
        url = f"https://{bucket}.s3.{current_app.config['AWS_S3_REGION']}.amazonaws.com/{unique_filename}"
        current_app.logger.info(f"File uploaded successfully: {url}")
        return url
        
    except ClientError as e:
        current_app.logger.error(f"S3 ClientError: {str(e)}")
        return None
    except Exception as e:
        current_app.logger.error(f"Unexpected error during upload: {str(e)}")
        return None