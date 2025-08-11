from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.settings import DATABASE_URL

import os

# DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./news.db")  # Default to SQLite for local development
# You can set this in your .env file or directly here.
# For development: "sqlite:///./news.db"
# for production: "postgresql://user:password@host:port/dbname"
from app.databases.models import Base
# Create the database engine
# Ensure you have the correct database URL in your .env file or set it directly here


engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create tables
def create_tables():
    Base.metadata.create_all(bind=engine)