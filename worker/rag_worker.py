import boto3
from io import BytesIO
from db import SessionLocal
import tempfile
from config import (AWS_ACCESS_KEY, AWS_SECRET_KEY, AWS_REGION, AWS_BUCKET_NAME, MAX_CHUNK_SIZE)
from doc_parsere import parse_document
from embedding import create_embeddings

MAX_MEMORY_SIZE = 20 * 1024 * 1024  # 20MB threshold
CHUNK_SIZE = 500      # characters
CHUNK_OVERLAP = 100   # overlap for context

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
        chunks = parse_document(file_stream,message["file_type"])

        # 3. Generate embeddings
        embeddings = create_embeddings(chunks, message)

        # 4. Store in DB (pgvector)
        save_embeddings(db, embeddings)

        db.commit()

    except Exception as e:
        db.rollback()
        raise

    finally:
        db.close()


def download_from_s3(s3_key: str):
    """
    Smart downloader:
    - Small files → memory
    - Large files → temp file
    """
    try:
        # Get metadata first
        head = s3_client.head_object(Bucket=BUCKET_NAME, Key=s3_key)
        file_size = head["ContentLength"]

        response = s3_client.get_object(Bucket=BUCKET_NAME, Key=s3_key)

        # SMALL FILE → MEMORY
        if file_size <= MAX_MEMORY_SIZE:
            file_stream = BytesIO()
            for chunk in response["Body"].iter_chunks(chunk_size=1024 * 1024):
                if chunk:
                    file_stream.write(chunk)

            file_stream.seek(0)
            return file_stream

        # LARGE FILE → TEMP FILE
        else:
            tmp_file = tempfile.NamedTemporaryFile(delete=False)

            for chunk in response["Body"].iter_chunks(chunk_size=1024 * 1024):
                if chunk:
                    tmp_file.write(chunk)

            tmp_file.flush()
            return tmp_file.name  # return file path

    except Exception as e:
        raise Exception(f"Error downloading {s3_key}: {str(e)}")