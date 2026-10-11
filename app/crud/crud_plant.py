from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.plant import Plant
from app.schemas.plant import PlantCreate, PlantUpdate


class CRUDPlant:
    """Data access methods for Plant entity."""

    def get(self, db: Session, plant_id: int) -> Optional[Plant]:
        return db.query(Plant).filter(Plant.id == plant_id).first()

    def list(
        self,
        db: Session,
        garden_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Plant]:
        query = db.query(Plant)
        if garden_id is not None:
            query = query.filter(Plant.garden_id == garden_id)
        return query.offset(skip).limit(limit).all()

    def create(self, db: Session, plant_in: PlantCreate) -> Plant:
        db_plant = Plant(
            garden_id=plant_in.garden_id,
            name=plant_in.name,
            species=plant_in.species,
            date_planted=plant_in.date_planted,
            location_in_garden=plant_in.location_in_garden,
            notes=plant_in.notes
        )
        db.add(db_plant)
        db.commit()
        db.refresh(db_plant)
        return db_plant

    def update(self, db: Session, db_obj: Plant, plant_in: PlantUpdate) -> Plant:
        update_data = plant_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def delete(self, db: Session, db_obj: Plant) -> None:
        db.delete(db_obj)
        db.commit()


plant_crud = CRUDPlant()

