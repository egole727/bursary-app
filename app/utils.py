import boto3
from botocore.exceptions import NoCredentialsError
from flask import current_app


def upload_file_to_s3(file, bucket):
    try:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=current_app.config['AWS_ACCESS_KEY_ID'],
            aws_secret_access_key=current_app.config['AWS_SECRET_ACCESS_KEY'],
            region_name=current_app.config['AWS_S3_REGION']
        )
        
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}-{filename}"
        
        s3_client.upload_fileobj(
            file,
            bucket,
            unique_filename,
            ExtraArgs={
                'ContentType': file.content_type,
                'ACL': 'public-read'
            }
        )
        
        return f"https://{bucket}.s3.{current_app.config['AWS_S3_REGION']}.amazonaws.com/{unique_filename}"
    except Exception as e:
        current_app.logger.error(f"S3 upload error: {str(e)}")
        return None
    """Upload a file to an S3 bucket and return the file URL."""
    s3 = boto3.client(
        "s3",
        aws_access_key_id=current_app.config["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=current_app.config["AWS_SECRET_ACCESS_KEY"],
        region_name=current_app.config["AWS_S3_REGION"],
    )

    try:
        s3.upload_fileobj(file, bucket_name, file.filename)
        return f"https://{bucket_name}.s3.amazonaws.com/{file.filename}"
    except NoCredentialsError:
        print("Credentials not available")
        return None
