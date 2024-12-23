import boto3
from botocore.exceptions import ClientError
from werkzeug.utils import secure_filename
import uuid

def upload_file_to_s3(file, bucket):
    # Validate inputs
    if not file or not hasattr(file, 'content_type'):
        current_app.logger.error("Invalid file object")
        return None
        
    if not bucket:
        current_app.logger.error("No bucket specified")
        return None

    try:
        # Debug logging
        current_app.logger.debug(f"File info - Name: {file.filename}, Type: {file.content_type}")
        current_app.logger.debug(f"AWS Config - Bucket: {bucket}, Region: {current_app.config['AWS_S3_REGION']}")
        
        s3_client = boto3.client(
            's3',
            aws_access_key_id=current_app.config['AWS_ACCESS_KEY_ID'],
            aws_secret_access_key=current_app.config['AWS_SECRET_ACCESS_KEY'],
            region_name=current_app.config['AWS_S3_REGION']
        )
        
        # Generate safe filename
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}-{filename}"
        
        # Upload with explicit content type
        file.seek(0)  # Reset file pointer
        s3_client.upload_fileobj(
            file,
            bucket,
            unique_filename,
            ExtraArgs={
                'ContentType': file.content_type or 'application/pdf',
                'ACL': 'public-read'
            }
        )
        
        url = f"https://{bucket}.s3.{current_app.config['AWS_S3_REGION']}.amazonaws.com/{unique_filename}"
        current_app.logger.info(f"File uploaded successfully: {url}")
        return url
        
    except ClientError as e:
        current_app.logger.error(f"AWS S3 error: {str(e)}")
        return None
    except AttributeError as e:
        current_app.logger.error(f"File object error: {str(e)}")
        return None
    except Exception as e:
        current_app.logger.error(f"Upload error: {str(e)}")
        return None