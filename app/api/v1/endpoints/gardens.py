from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.crud.crud_garden import garden_crud
from app.crud.crud_user import user_crud
from app.schemas.garden import GardenCreate, GardenUpdate, GardenResponse

router = APIRouter()


@router.post("/", response_model=GardenResponse, status_code=status.HTTP_201_CREATED)
def create_garden(
    garden_in: GardenCreate,
    db: Session = Depends(get_db)
):
    """Create a new garden associated with a user."""
    user = user_crud.get(db=db, user_id=garden_in.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with ID {garden_in.user_id} does not exist."
        )
    return garden_crud.create(db=db, garden_in=garden_in)


@router.get("/", response_model=List[GardenResponse])
def list_gardens(
    user_id: Optional[int] = Query(None, description="Filter gardens by owner user ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """List gardens, optionally filtered by user ID."""
    return garden_crud.list(db=db, user_id=user_id, skip=skip, limit=limit)


@router.get("/{garden_id}", response_model=GardenResponse)
def get_garden(
    garden_id: int,
    db: Session = Depends(get_db)
):
    """Retrieve garden details by ID."""
    garden = garden_crud.get(db=db, garden_id=garden_id)
    if not garden:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Garden with ID {garden_id} not found."
        )
    return garden


@router.put("/{garden_id}", response_model=GardenResponse)
def update_garden(
    garden_id: int,
    garden_in: GardenUpdate,
    db: Session = Depends(get_db)
):
    """Update garden attributes (name, location, sunlight, etc.)."""
    garden = garden_crud.get(db=db, garden_id=garden_id)
    if not garden:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Garden with ID {garden_id} not found."
        )
    return garden_crud.update(db=db, db_obj=garden, garden_in=garden_in)


@router.delete("/{garden_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_garden(
    garden_id: int,
    db: Session = Depends(get_db)
):
    """Delete a garden and its associated plants/tasks."""
    garden = garden_crud.get(db=db, garden_id=garden_id)
    if not garden:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Garden with ID {garden_id} not found."
        )
    garden_crud.delete(db=db, db_obj=garden)
    return None

