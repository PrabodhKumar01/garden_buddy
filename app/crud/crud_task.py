from datetime import date, datetime, timezone
from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.task import GardenTask
from app.schemas.task import TaskCreate, TaskUpdate, TaskStatusUpdate


class CRUDTask:
    """Data access methods for GardenTask entity."""

    def get(self, db: Session, task_id: int) -> Optional[GardenTask]:
        return db.query(GardenTask).filter(GardenTask.id == task_id).first()

    def list(
        self,
        db: Session,
        garden_id: Optional[int] = None,
        plant_id: Optional[int] = None,
        target_date: Optional[date] = None,
        is_completed: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[GardenTask]:
        query = db.query(GardenTask)
        if garden_id is not None:
            query = query.filter(GardenTask.garden_id == garden_id)
        if plant_id is not None:
            query = query.filter(GardenTask.plant_id == plant_id)
        if target_date is not None:
            query = query.filter(GardenTask.task_date == target_date)
        if is_completed is not None:
            query = query.filter(GardenTask.is_completed == is_completed)
        return query.order_by(GardenTask.task_date.desc(), GardenTask.id.desc()).offset(skip).limit(limit).all()

    def get_todays_tasks(
        self,
        db: Session,
        garden_id: int,
        target_date: Optional[date] = None
    ) -> List[GardenTask]:
        """Retrieve tasks scheduled for today (or specified date) for a specific garden."""
        check_date = target_date or date.today()
        return (
            db.query(GardenTask)
            .filter(
                GardenTask.garden_id == garden_id,
                GardenTask.task_date == check_date
            )
            .order_by(GardenTask.is_completed.asc(), GardenTask.id.asc())
            .all()
        )

    def create(self, db: Session, task_in: TaskCreate) -> GardenTask:
        db_task = GardenTask(
            garden_id=task_in.garden_id,
            plant_id=task_in.plant_id,
            title=task_in.title,
            description=task_in.description,
            category=task_in.category,
            task_date=task_in.task_date,
            is_completed=task_in.is_completed,
            source=task_in.source
        )
        if task_in.is_completed:
            db_task.completed_at = datetime.now(timezone.utc)
        db.add(db_task)
        db.commit()
        db.refresh(db_task)
        return db_task

    def update(self, db: Session, db_obj: GardenTask, task_in: TaskUpdate) -> GardenTask:
        update_data = task_in.model_dump(exclude_unset=True)
        # Handle completed_at timestamp sync if is_completed changed
        if "is_completed" in update_data:
            if update_data["is_completed"] and not db_obj.is_completed:
                db_obj.completed_at = datetime.now(timezone.utc)
            elif not update_data["is_completed"]:
                db_obj.completed_at = None

        for field, value in update_data.items():
            setattr(db_obj, field, value)

        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update_status(self, db: Session, db_obj: GardenTask, status_in: TaskStatusUpdate) -> GardenTask:
        """Mark task as complete/incomplete and record optional observation notes."""
        db_obj.is_completed = status_in.is_completed
        if status_in.is_completed:
            db_obj.completed_at = datetime.now(timezone.utc)
        else:
            db_obj.completed_at = None

        if status_in.result_notes is not None:
            db_obj.result_notes = status_in.result_notes

        db.commit()
        db.refresh(db_obj)
        return db_obj

    def delete(self, db: Session, db_obj: GardenTask) -> None:
        db.delete(db_obj)
        db.commit()


task_crud = CRUDTask()

