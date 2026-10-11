from datetime import date, datetime
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models.user import User
from app.models.garden import Garden
from app.models.plant import Plant
from app.models.task import GardenTask
from app.schemas.task import TaskCreate, TaskStatusUpdate, TaskResponse


@pytest.fixture
def db_session():
    """Create an in-memory SQLite session for testing models."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def test_create_user_and_garden(db_session):
    user = User(username="gardener1", email="gardener@example.com")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    assert user.id is not None
    assert user.username == "gardener1"

    garden = Garden(
        user_id=user.id,
        name="Sunny Balcony",
        location="Seattle, WA",
        garden_type="Balcony",
        sunlight="Full Sun"
    )
    db_session.add(garden)
    db_session.commit()
    db_session.refresh(garden)

    assert garden.id is not None
    assert garden.user.username == "gardener1"
    assert len(user.gardens) == 1


def test_create_plant_and_task(db_session):
    user = User(username="greenthumb", email="green@example.com")
    db_session.add(user)
    db_session.commit()

    garden = Garden(user_id=user.id, name="Veggie Patch", location="Austin, TX")
    db_session.add(garden)
    db_session.commit()

    plant = Plant(
        garden_id=garden.id,
        name="Tomato",
        species="Solanum lycopersicum",
        date_planted=date(2026, 4, 15)
    )
    db_session.add(plant)
    db_session.commit()
    db_session.refresh(plant)

    assert plant.id is not None
    assert plant.garden_id == garden.id

    # Create daily garden task
    task = GardenTask(
        garden_id=garden.id,
        plant_id=plant.id,
        title="Check tomato leaves for yellowing",
        description="Inspect underleaves for pests and trim any yellow foliage.",
        category="inspection",
        task_date=date.today(),
        is_completed=False,
        source="ai_generated"
    )
    db_session.add(task)
    db_session.commit()
    db_session.refresh(task)

    assert task.id is not None
    assert task.is_completed is False
    assert task.plant.name == "Tomato"
    assert task.garden.name == "Veggie Patch"

    # Mark completed
    task.is_completed = True
    task.completed_at = datetime.now()
    db_session.commit()
    db_session.refresh(task)

    assert task.is_completed is True
    assert task.completed_at is not None


def test_task_schema_validation():
    # Test valid TaskCreate schema
    data = {
        "garden_id": 1,
        "title": "Water the mint",
        "description": "Give 500ml water in morning",
        "category": "watering",
        "task_date": date.today(),
        "is_completed": False,
        "source": "ai_generated"
    }
    task_in = TaskCreate(**data)
    assert task_in.title == "Water the mint"
    assert task_in.garden_id == 1

    # Test TaskStatusUpdate schema
    status_update = TaskStatusUpdate(is_completed=True)
    assert status_update.is_completed is True

