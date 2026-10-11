from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.crud.crud_garden import garden_crud
from app.crud.crud_plant import plant_crud
from app.crud.crud_task import task_crud
from app.schemas.task import TaskCreate, TaskUpdate, TaskStatusUpdate, TaskResponse
from app.services.task_completion import task_completion_service

router = APIRouter()


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(
    task_in: TaskCreate,
    db: Session = Depends(get_db)
):
    """Create a new garden task."""
    garden = garden_crud.get(db=db, garden_id=task_in.garden_id)
    if not garden:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Garden with ID {task_in.garden_id} does not exist."
        )

    if task_in.plant_id is not None:
        plant = plant_crud.get(db=db, plant_id=task_in.plant_id)
        if not plant or plant.garden_id != task_in.garden_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Plant with ID {task_in.plant_id} does not belong to garden {task_in.garden_id}."
            )

    return task_crud.create(db=db, task_in=task_in)


@router.get("/today", response_model=List[TaskResponse])
def get_todays_tasks(
    garden_id: int = Query(..., description="Garden ID to fetch today's plan for"),
    target_date: Optional[date] = Query(None, description="Optional date (defaults to today)"),
    db: Session = Depends(get_db)
):
    """Retrieve today's tasks for a specific garden (Phase 3.3)."""
    garden = garden_crud.get(db=db, garden_id=garden_id)
    if not garden:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Garden with ID {garden_id} not found."
        )
    return task_crud.get_todays_tasks(db=db, garden_id=garden_id, target_date=target_date)


@router.get("/", response_model=List[TaskResponse])
def list_tasks(
    garden_id: Optional[int] = Query(None, description="Filter by garden ID"),
    plant_id: Optional[int] = Query(None, description="Filter by plant ID"),
    task_date: Optional[date] = Query(None, description="Filter by scheduled date"),
    is_completed: Optional[bool] = Query(None, description="Filter by completion status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """List tasks with optional filters."""
    return task_crud.list(
        db=db,
        garden_id=garden_id,
        plant_id=plant_id,
        target_date=task_date,
        is_completed=is_completed,
        skip=skip,
        limit=limit
    )


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: int,
    db: Session = Depends(get_db)
):
    """Retrieve task details by ID."""
    task = task_crud.get(db=db, task_id=task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} not found."
        )
    return task


@router.patch("/{task_id}/complete", response_model=TaskResponse)
async def mark_task_complete(
    task_id: int,
    status_in: TaskStatusUpdate,
    db: Session = Depends(get_db)
):
    """Mark task completed, update garden/plant state, and record observations/memories (Phase 11)."""
    task = await task_completion_service.complete_task(db=db, task_id=task_id, status_in=status_in)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} not found."
        )
    return task


@router.put("/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: int,
    task_in: TaskUpdate,
    db: Session = Depends(get_db)
):
    """Update task details."""
    task = task_crud.get(db=db, task_id=task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} not found."
        )
    return task_crud.update(db=db, db_obj=task, task_in=task_in)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db)
):
    """Delete a task."""
    task = task_crud.get(db=db, task_id=task_id)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} not found."
        )
    task_crud.delete(db=db, db_obj=task)
    return None

