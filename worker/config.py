from dotenv import load_dotenv
import os
load_dotenv()

DATABASE_USER= os.getenv("DATABASE_USER")
DATABASE_PASSWORD= os.getenv("DATABASE_PASSWORD")
DATABASE_HOST= os.getenv("DATABASE_HOST")
DATABASE_NAME= os.getenv("DATABASE_NAME")
DATABASE_SSL_MODE= os.getenv("DATABASE_SSL_MODE")

AWS_ACCESS_KEY= os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_KEY= os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION= os.getenv("AWS_REGION")
AWS_BUCKET_NAME= os.getenv("AWS_BUCKET_NAME")
ALLOWED_TYPES= os.getenv("ALLOWED_TYPES").split(",")
MAX_CHUNK_SIZE= int(os.getenv("MAX_CHUNK_SIZE"))