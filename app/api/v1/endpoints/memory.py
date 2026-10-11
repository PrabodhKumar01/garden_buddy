from typing import Any, Dict, Optional
from fastapi import APIRouter, HTTPException, Query, status

from app.schemas.memory import (
    MemoryCreate,
    MemoryQueryResponse,
    MemoryResponse,
)
from app.services.backboard import backboard_service

router = APIRouter()


@router.post("/", response_model=MemoryResponse, status_code=status.HTTP_201_CREATED)
async def create_memory(memory_in: MemoryCreate) -> MemoryResponse:
    """Store a useful gardening memory (preference, observation, history, habit) in Backboard."""
    return await backboard_service.create_memory(memory_in=memory_in)


@router.get("/", response_model=MemoryQueryResponse)
async def query_memories(
    user_id: int = Query(..., description="User ID to retrieve memories for"),
    garden_id: Optional[int] = Query(None, description="Optional garden ID filter"),
    query: Optional[str] = Query(None, description="Topic or situation to filter memories"),
    limit: int = Query(5, ge=1, le=20, description="Max memories to return")
) -> MemoryQueryResponse:
    """Retrieve relevant memories for a user and garden."""
    return await backboard_service.retrieve_memories(
        user_id=user_id,
        garden_id=garden_id,
        query=query,
        limit=limit
    )


@router.get("/connectivity")
async def check_backboard_connectivity() -> Dict[str, Any]:
    """Verify connectivity and configuration status of Backboard.io."""
    return await backboard_service.check_connection()

