from sqlalchemy import Column, Integer, String, Text, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Plant(Base):
    """Plant entity representing a plant in a specific garden."""

    __tablename__ = "plants"

    id = Column(Integer, primary_key=True, index=True)
    garden_id = Column(Integer, ForeignKey("gardens.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)  # e.g., Tomato, Coriander, Spinach
    species = Column(String(150), nullable=True)  # Scientific name or specific cultivar
    date_planted = Column(Date, nullable=True)
    location_in_garden = Column(String(150), nullable=True)  # e.g., Bed 1, Container A
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    garden = relationship("Garden", back_populates="plants")
    tasks = relationship("GardenTask", back_populates="plant", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Plant(id={self.id}, name='{self.name}', garden_id={self.garden_id})>"

