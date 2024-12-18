import boto3
from botocore.exceptions import NoCredentialsError
from flask import current_app

def upload_file_to_s3(file, bucket_name):
    """Upload a file to an S3 bucket and return the file URL."""
    s3 = boto3.client(
        's3',
        aws_access_key_id=current_app.config['AWS_ACCESS_KEY_ID'],
        aws_secret_access_key=current_app.config['AWS_SECRET_ACCESS_KEY'],
        region_name=current_app.config['AWS_S3_REGION']
    )
    
    try:
        s3.upload_fileobj(file, bucket_name, file.filename)
        return f"https://{bucket_name}.s3.amazonaws.com/{file.filename}"
    except NoCredentialsError:
        print("Credentials not available")
        return None