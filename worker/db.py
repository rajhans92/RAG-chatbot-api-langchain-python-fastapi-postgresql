from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from config import (
    DATABASE_USER, DATABASE_PASSWORD,
    DATABASE_HOST, DATABASE_PORT, DATABASE_NAME
)

DATABASE_URL = f"mysql+pymysql://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}/{DATABASE_NAME}"

engine = create_engine(
    DATABASE_URL,
    pool_size=5,          # important
    max_overflow=10,
    pool_pre_ping=True    # avoids stale connections
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()