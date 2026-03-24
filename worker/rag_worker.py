import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from io import BytesIO
import time

from db import SessionLocal
from config import (AWS_ACCESS_KEY, AWS_SECRET_KEY, AWS_REGION, AWS_BUCKET_NAME, MAX_CHUNK_SIZE)

s3_client = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY,
    region_name=AWS_REGION
)

BUCKET_NAME = AWS_BUCKET_NAME

def process_file(message):
    db = SessionLocal()

    try:
        # 1. Download file from S3
        file_stream = download_from_s3(message["s3_url"])

        # 2. Parse
        chunks = parse_document(file_stream)

        # 3. Generate embeddings
        embeddings = create_embeddings(chunks)

        # 4. Store in DB (pgvector)
        save_embeddings(db, embeddings)

        db.commit()

    except Exception as e:
        db.rollback()
        raise

    finally:
        db.close()


def download_from_s3(s3_key) -> BytesIO:
    """
    Download file from S3 into memory (BytesIO).
    Best for small/medium files.
    """
    try:
        response = s3_client.get_object(Bucket=BUCKET_NAME, Key=s3_key)

        file_stream = BytesIO()
        
        # Stream read (avoids loading everything at once)
        for chunk in response["Body"].iter_chunks(chunk_size=MAX_CHUNK_SIZE):  # 1MB chunks
            if chunk:
                file_stream.write(chunk)

        file_stream.seek(0)
        return file_stream

    except ClientError as e:
        error_code = e.response["Error"]["Code"]

        if error_code == "NoSuchKey":
            raise Exception(f"File not found in S3: {s3_key}")
        elif error_code == "AccessDenied":
            raise Exception(f"Access denied for S3 key: {s3_key}")
        else:
            raise Exception(f"S3 download failed: {str(e)}")

    except Exception as e:
        raise Exception(f"Unexpected error downloading {s3_key}: {str(e)}")

def parse_document(file_stream):
    # Implement document parsing logic here (e.g., using PyPDF2, python-docx, etc.)
    pass

def create_embeddings(chunks):
    # Implement embedding generation logic here (e.g., using OpenAI API)
    pass

def save_embeddings(db, embeddings):
    # Implement logic to save embeddings in the database (e.g., using SQLAlchemy)
    pass