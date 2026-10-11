from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.crud.crud_garden import garden_crud
from app.crud.crud_plant import plant_crud
from app.schemas.plant import PlantCreate, PlantUpdate, PlantResponse

router = APIRouter()


@router.post("/", response_model=PlantResponse, status_code=status.HTTP_201_CREATED)
def add_plant(
    plant_in: PlantCreate,
    db: Session = Depends(get_db)
):
    """Add a plant to a specific garden."""
    garden = garden_crud.get(db=db, garden_id=plant_in.garden_id)
    if not garden:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Garden with ID {plant_in.garden_id} does not exist."
        )
    return plant_crud.create(db=db, plant_in=plant_in)


@router.get("/", response_model=List[PlantResponse])
def list_plants(
    garden_id: Optional[int] = Query(None, description="Filter plants by garden ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """Retrieve plants, optionally filtered by garden ID."""
    return plant_crud.list(db=db, garden_id=garden_id, skip=skip, limit=limit)


@router.get("/{plant_id}", response_model=PlantResponse)
def get_plant(
    plant_id: int,
    db: Session = Depends(get_db)
):
    """Retrieve plant details by ID."""
    plant = plant_crud.get(db=db, plant_id=plant_id)
    if not plant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plant with ID {plant_id} not found."
        )
    return plant


@router.put("/{plant_id}", response_model=PlantResponse)
def update_plant(
    plant_id: int,
    plant_in: PlantUpdate,
    db: Session = Depends(get_db)
):
    """Update plant information."""
    plant = plant_crud.get(db=db, plant_id=plant_id)
    if not plant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plant with ID {plant_id} not found."
        )
    return plant_crud.update(db=db, db_obj=plant, plant_in=plant_in)


@router.delete("/{plant_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_plant(
    plant_id: int,
    db: Session = Depends(get_db)
):
    """Remove a plant from a garden."""
    plant = plant_crud.get(db=db, plant_id=plant_id)
    if not plant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Plant with ID {plant_id} not found."
        )
    plant_crud.delete(db=db, db_obj=plant)
    return None

