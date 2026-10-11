from app.core.database import check_db_connection, get_db, SessionLocal
from sqlalchemy.orm import Session


def test_database_connection_checker():
    """Verify that check_db_connection returns a structured dictionary."""
    status = check_db_connection()
    assert isinstance(status, dict)
    assert "connected" in status
    assert isinstance(status["connected"], bool)
    assert "message" in status
    assert isinstance(status["message"], str)


def test_get_db_generator():
    """Verify get_db dependency yields a database Session."""
    assert SessionLocal is not None
    db_gen = get_db()
    db = next(db_gen)
    assert isinstance(db, Session)
    # Safely close generator
    try:
        next(db_gen)
    except StopIteration:
        pass

