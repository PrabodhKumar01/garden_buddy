from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.garden import Garden
from app.schemas.garden import GardenCreate, GardenUpdate


class CRUDGarden:
    """Data access methods for Garden entity."""

    def get(self, db: Session, garden_id: int) -> Optional[Garden]:
        return db.query(Garden).filter(Garden.id == garden_id).first()

    def list(
        self,
        db: Session,
        user_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Garden]:
        query = db.query(Garden)
        if user_id is not None:
            query = query.filter(Garden.user_id == user_id)
        return query.offset(skip).limit(limit).all()

    def create(self, db: Session, garden_in: GardenCreate) -> Garden:
        db_garden = Garden(
            user_id=garden_in.user_id,
            name=garden_in.name,
            location=garden_in.location,
            garden_type=garden_in.garden_type,
            sunlight=garden_in.sunlight,
            notes=garden_in.notes
        )
        db.add(db_garden)
        db.commit()
        db.refresh(db_garden)
        return db_garden

    def update(self, db: Session, db_obj: Garden, garden_in: GardenUpdate) -> Garden:
        update_data = garden_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def delete(self, db: Session, db_obj: Garden) -> None:
        db.delete(db_obj)
        db.commit()


garden_crud = CRUDGarden()

