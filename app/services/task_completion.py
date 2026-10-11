import logging
from datetime import date
from typing import Optional
from sqlalchemy.orm import Session

from app.crud.crud_plant import plant_crud
from app.crud.crud_garden import garden_crud
from app.crud.crud_task import task_crud
from app.models.task import GardenTask
from app.schemas.memory import MemoryCreate, MemoryType
from app.schemas.task import TaskStatusUpdate
from app.services.backboard import backboard_service

logger = logging.getLogger(__name__)


class TaskCompletionService:
    """Service handling Phase 11 Task Completion workflows.

    Coordinates:
    - Task completion status updates
    - Garden & Plant state synchronization
    - Meaningful AI memory persistence to Backboard.io
    """

    async def complete_task(
        self,
        db: Session,
        task_id: int,
        status_in: TaskStatusUpdate
    ) -> Optional[GardenTask]:
        """Complete or update a task, updating garden state and AI memory as needed."""
        task = task_crud.get(db=db, task_id=task_id)
        if not task:
            return None

        # 1. Update task completion in PostgreSQL
        updated_task = task_crud.update_status(db=db, db_obj=task, status_in=status_in)

        # 2. If task was marked completed, synchronize state & memory
        if status_in.is_completed:
            await self._sync_garden_state_and_memory(db=db, task=updated_task, status_in=status_in)

        return updated_task

    async def _sync_garden_state_and_memory(
        self,
        db: Session,
        task: GardenTask,
        status_in: TaskStatusUpdate
    ) -> None:
        """Update plant/garden records and create relevant Backboard memories."""
        plant = None
        if task.plant_id:
            plant = plant_crud.get(db=db, plant_id=task.plant_id)

        garden = task.garden or garden_crud.get(db=db, garden_id=task.garden_id)
        user_id = garden.user_id if garden else 1
        plant_display_name = plant.name if plant else "Garden"

        # A. Update Garden / Plant structured state
        if status_in.result_notes:
            today_str = date.today().isoformat()
            obs_log = f"[{today_str}] {status_in.result_notes}"
            if plant:
                plant.notes = f"{plant.notes}\n{obs_log}" if plant.notes else obs_log
                db.add(plant)
                db.commit()
                db.refresh(plant)
            elif garden:
                garden.notes = f"{garden.notes}\n{obs_log}" if garden.notes else obs_log
                db.add(garden)
                db.commit()
                db.refresh(garden)

        # B. Sync meaningful memory to Backboard.io
        try:
            # 1. Direct gardener observation
            if status_in.result_notes and status_in.result_notes.strip():
                await backboard_service.create_memory(
                    MemoryCreate(
                        user_id=user_id,
                        garden_id=task.garden_id,
                        plant_id=task.plant_id,
                        memory_type=MemoryType.OBSERVATION,
                        content=f"{plant_display_name}: {status_in.result_notes.strip()} (Task: {task.title})",
                        importance=4
                    )
                )
                logger.info(f"Recorded observation memory for task {task.id} in Backboard.")

            # 2. Key gardening events (Watering & Harvest tracking)
            category = (task.category or "").lower()
            if category == "watering":
                await backboard_service.create_memory(
                    MemoryCreate(
                        user_id=user_id,
                        garden_id=task.garden_id,
                        plant_id=task.plant_id,
                        memory_type=MemoryType.HISTORY,
                        content=f"Watered {plant_display_name} on {date.today()}.",
                        importance=3
                    )
                )
                logger.info(f"Recorded watering history memory for {plant_display_name}.")
            elif category == "harvest":
                await backboard_service.create_memory(
                    MemoryCreate(
                        user_id=user_id,
                        garden_id=task.garden_id,
                        plant_id=task.plant_id,
                        memory_type=MemoryType.HISTORY,
                        content=f"Harvested {plant_display_name} on {date.today()}.",
                        importance=3
                    )
                )
                logger.info(f"Recorded harvest history memory for {plant_display_name}.")

        except Exception as exc:
            # Memory failure should never block core application task completion
            logger.warning(f"Failed to record Backboard memory for task {task.id}: {exc}")


task_completion_service = TaskCompletionService()
