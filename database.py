"""
Database Connection and Session Management
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import StaticPool
from models import Base

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///ehr_database.db")

# Create engine
# For SQLite, use check_same_thread=False and StaticPool for better concurrency
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=False  # Set to True for SQL query logging
    )
else:
    # For PostgreSQL or other databases
    engine = create_engine(DATABASE_URL, pool_pre_ping=True, echo=False)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Thread-safe session
Session = scoped_session(SessionLocal)


def init_database():
    """Initialize database - create all tables"""
    print("Initializing database...")
    Base.metadata.create_all(bind=engine)
    print("✓ Database tables created successfully")


def get_db():
    """Get database session - use with context manager"""
    db = Session()
    try:
        yield db
    finally:
        db.close()


def get_db_session():
    """Get database session - manual management"""
    return Session()


def close_db_session(db):
    """Close database session"""
    db.close()


if __name__ == "__main__":
    # Initialize database when run directly
    init_database()
    print("Database initialized!")
