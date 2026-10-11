from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.crud.crud_garden import garden_crud
from app.schemas.ai_plan import DailyGardenPlan, GeneratePlanRequest
from app.services.thinking_machines import thinking_machines_service

router = APIRouter()


@router.post("/daily-plan", response_model=DailyGardenPlan, status_code=status.HTTP_200_OK)
async def generate_daily_garden_plan(
    plan_in: GeneratePlanRequest,
    db: Session = Depends(get_db)
) -> DailyGardenPlan:
    """Generate today's personalized AI Garden Plan synthesizing weather, plants, RAG, and memory."""
    garden = garden_crud.get(db=db, garden_id=plan_in.garden_id)
    if not garden:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Garden with ID {plan_in.garden_id} not found."
        )

    try:
        return await thinking_machines_service.generate_daily_plan(
            db=db,
            garden_id=plan_in.garden_id,
            target_date=plan_in.target_date,
            save_tasks_to_db=plan_in.save_tasks_to_db
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate daily garden plan: {str(exc)}"
        )


@router.get("/daily-plan/{garden_id}", response_model=DailyGardenPlan)
async def get_daily_garden_plan(
    garden_id: int,
    target_date: Optional[date] = Query(None, description="Optional target date, defaults to today"),
    save_tasks_to_db: bool = Query(True, description="Whether to save generated tasks to database"),
    db: Session = Depends(get_db)
) -> DailyGardenPlan:
    """Convenience GET endpoint to generate or view today's plan for a garden."""
    garden = garden_crud.get(db=db, garden_id=garden_id)
    if not garden:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Garden with ID {garden_id} not found."
        )

    return await thinking_machines_service.generate_daily_plan(
        db=db,
        garden_id=garden_id,
        target_date=target_date,
        save_tasks_to_db=save_tasks_to_db
    )

