from datetime import date
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.crud.crud_garden import garden_crud
from app.schemas.ai_plan import DailyGardenPlan, GeneratePlanRequest
from app.services.daily_garden_agent import daily_garden_agent

router = APIRouter()


@router.post("/plan", response_model=DailyGardenPlan, status_code=status.HTTP_200_OK)
async def generate_agent_plan(
    plan_in: GeneratePlanRequest,
    db: Session = Depends(get_db)
) -> DailyGardenPlan:
    """Execute the end-to-end Daily Garden Agent workflow (Phase 9).

    Orchestrates: Garden state + Plants + Memory + Weather Tool + RAG -> Thinking Machines -> Plan.
    """
    try:
        return await daily_garden_agent.execute_daily_workflow(
            db=db,
            garden_id=plan_in.garden_id,
            target_date=plan_in.target_date,
            save_to_database=plan_in.save_tasks_to_db
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc)
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent workflow encountered an error: {str(exc)}"
        )


@router.get("/plan/{garden_id}", response_model=None)
async def get_agent_plan(
    garden_id: int,
    target_date: Optional[date] = Query(None, description="Plan date (defaults to today)"),
    format_markdown: bool = Query(False, description="Whether to include formatted markdown checklist"),
    save_tasks: bool = Query(True, description="Whether to persist tasks to database"),
    db: Session = Depends(get_db)
) -> Any:
    """Convenience endpoint to retrieve or generate Today's Garden Plan for a garden."""
    try:
        plan = await daily_garden_agent.execute_daily_workflow(
            db=db,
            garden_id=garden_id,
            target_date=target_date,
            save_to_database=save_tasks
        )
        if format_markdown:
            return {
                "plan": plan.model_dump(),
                "markdown": daily_garden_agent.format_plan_as_markdown(plan)
            }
        return plan
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc)
        )

