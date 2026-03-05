"""
Database connection and session management for Case-Verify AI

P-04 / Hardening Plan: Adds ``db_session()`` context manager for safe,
automatic session lifecycle (commit-on-success, rollback-on-error, close-always).
"""
import os
import logging
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from typing import Generator

# Import Base from models to avoid circular imports
from database.models import Base

logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./case_verify.db")

# Create engine with connection pooling for SQLite
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    poolclass=StaticPool if "sqlite" in DATABASE_URL else None,
    echo=False  # Set to True for debugging SQL queries
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ---------------------------------------------------------------------------
# P-04: Context manager for safe session lifecycle
# ---------------------------------------------------------------------------

@contextmanager
def db_session() -> Generator[Session, None, None]:
    """
    Context manager that provides a transactional database session.

    Usage::

        from database.connection import db_session

        with db_session() as db:
            user = db.query(User).filter_by(username="admin").first()
            user.last_login = datetime.now(timezone.utc)
            # auto-commits on clean exit, auto-rollbacks on exception

    The session is **always closed** when the block exits.
    """
    session: Session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_db() -> Generator:
    """
    Dependency function to get database session (legacy / FastAPI-style).
    Prefer ``db_session()`` context manager for new code.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_database():
    """
    Initialize database tables
    """
    from database.models import Base
    Base.metadata.create_all(bind=engine)
    print("Database initialized successfully!")

def reset_database():
    """
    Reset database - WARNING: This will delete all data!
    """
    from database.models import Base
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("Database reset successfully!")
