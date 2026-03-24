from dotenv import load_dotenv
import os
load_dotenv()

DATABASE_USER= os.getenv("DATABASE_USER")
DATABASE_PASSWORD= os.getenv("DATABASE_PASSWORD")
DATABASE_HOST= os.getenv("DATABASE_HOST")
DATABASE_NAME= os.getenv("DATABASE_NAME")
DATABASE_SSL_MODE= os.getenv("DATABASE_SSL_MODE")