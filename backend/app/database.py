from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from .config import settings

import os

# Create SQLAlchemy engine with connection pooling for Supabase/PostgreSQL
engine = create_engine(
    os.getenv("DATABASE_URL"),  # Use DATABASE_URL from environment
    pool_size=20,  # Maximum number of persistent connections in the pool
    max_overflow=10,  # Maximum number of connections that can be created beyond pool_size
    pool_pre_ping=True,  # Enable connection health checks
    pool_recycle=300,  # Recycle connections after 5 minutes (Supabase recommended)
    echo=False,  # Set to True for SQL query logging in development
)

# Create SessionLocal class for database sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for declarative models
Base = declarative_base()

def get_db():
    """
    Dependency function to get database session.
    Use in FastAPI route dependencies: Depends(get_db)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
