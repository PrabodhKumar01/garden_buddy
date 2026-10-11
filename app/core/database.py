from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

# Base class for SQLAlchemy declarative models
Base = declarative_base()

# SQLAlchemy Engine and SessionLocal
# Handle SQLite / PostgreSQL connection arguments appropriately
connect_args = {}
db_url = settings.DATABASE_URL

if db_url:
    # Normalize Render's postgres:// to postgresql://
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql+psycopg2://", 1)
    elif db_url.startswith("postgresql://") and not db_url.startswith("postgresql+"):
        db_url = db_url.replace("postgresql://", "postgresql+psycopg2://", 1)

    if db_url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}

engine = None
SessionLocal = None

if db_url:
    try:
        engine = create_engine(
            db_url,
            connect_args=connect_args,
            pool_pre_ping=True
        )
        SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=engine
        )
    except Exception as e:
        logger.warning(f"Could not initialize database engine: {e}")


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency to yield a database session per request."""
    if SessionLocal is None:
        raise RuntimeError("Database engine is not configured or available.")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create database tables for all registered models with resilient SQLite fallback.

    If PostgreSQL credentials fail or PostgreSQL is unreachable locally,
    falls back to local SQLite ('sqlite:///./gardenbuddy.db') so the application
    works immediately out of the box without crashing.
    """
    global engine, SessionLocal
    import app.models  # noqa: F401

    if engine is not None:
        try:
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            Base.metadata.create_all(bind=engine)
            logger.info("Database tables initialized successfully on primary database.")
            return
        except Exception as e:
            logger.warning(
                f"Primary database connection/authentication failed ({e}). "
                "Falling back to local SQLite database ('sqlite:///./gardenbuddy.db') for seamless development."
            )

    # Resilient fallback to local SQLite
    try:
        sqlite_url = "sqlite:///./gardenbuddy.db"
        engine = create_engine(sqlite_url, connect_args={"check_same_thread": False}, pool_pre_ping=True)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        Base.metadata.create_all(bind=engine)
        logger.info("Local SQLite database ('gardenbuddy.db') initialized successfully.")
    except Exception as exc:
        logger.error(f"Error creating fallback database tables: {exc}")


def check_db_connection() -> dict:
    """Verify connectivity to database.

    Returns:
        dict: Connection status details.
    """
    if engine is None:
        return {
            "connected": False,
            "message": "Database engine is not configured (DATABASE_URL is empty)"
        }
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_type = "sqlite" if str(engine.url).startswith("sqlite") else "postgresql"
        return {
            "connected": True,
            "database_type": db_type,
            "message": f"Database connection successful ({db_type})"
        }
    except Exception as e:
        return {
            "connected": False,
            "message": f"Database connection error: {str(e)}"
        }

