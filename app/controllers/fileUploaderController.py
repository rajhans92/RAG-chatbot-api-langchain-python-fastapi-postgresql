import boto3
from botocore.exceptions import ClientError
from app.helpers.config import (AWS_ACCESS_KEY, AWS_SECRET_KEY, AWS_REGION, AWS_BUCKET_NAME)
from app.models.documentModel import Documents


class S3Service:
    def __init__(self):
        self.s3 = boto3.client(
            "s3",
            aws_access_key_id=AWS_ACCESS_KEY,
            aws_secret_access_key=AWS_SECRET_KEY,
            region_name=AWS_REGION
        )
        self.bucket_name = AWS_BUCKET_NAME

    def upload_file(self, file_obj, object_name, content_type, user_id, session_id):
        try:
            key = f"{user_id}/{session_id}/{object_name}"
            self.s3.upload_fileobj(file_obj, self.bucket_name, key, ExtraArgs={"ContentType": content_type})
            return f"https://{self.bucket_name}.s3.{AWS_REGION}.amazonaws.com/{key}"
        except ClientError as e:
            print(f"S3 Upload Error: {e}")
            return None

# Create a single instance to be imported elsewhere
s3Service = S3Service()

async def storeFiledetails(original_name, unique_name, s3_url, content_type, user_id, session_id, db):
    try:
        new_document = Documents(
            user_id=user_id,
            session_id=session_id,
            document_name=original_name,
            document_unique_name=unique_name,
            document_type=content_type,
            storage_path=s3_url,
            status="processing"
        )
        db.add(new_document)
        await db.commit()
        await db.refresh(new_document)
        return new_document.id
    except Exception as e:
        print(f"Database Error: {e}")
        return None