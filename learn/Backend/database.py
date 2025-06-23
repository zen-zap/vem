from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from typing import Generator

# Define the database URL (using SQLite for local storage)
DATABASE_URL = "sqlite:///./items.db"

# Create the database engine
# connect_args is required for SQLite to allow usage with multiple threads (needed for FastAPI)
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# Create a configured "Session" class for database sessions
SessionLocal = sessionmaker(bind=engine)

# Base class for our ORM models (tables will inherit from this)
Base = declarative_base()

# Dependency function to get a database session for each request
# Yields a session to the caller and ensures it is closed after use
def get_db() -> Generator:
    db = SessionLocal()      # Create a new database session
    try:
        yield db            # Yield the session to be used in API endpoints
    finally:
        db.close()          # Ensure the session is closed after the request is handled
