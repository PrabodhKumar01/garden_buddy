from sqlalchemy import Column, Integer, String, Text, Boolean, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class GardenTask(Base):
    """GardenTask entity representing a daily task to be completed outdoors."""

    __tablename__ = "garden_tasks"

    id = Column(Integer, primary_key=True, index=True)
    garden_id = Column(Integer, ForeignKey("gardens.id", ondelete="CASCADE"), nullable=False, index=True)
    plant_id = Column(Integer, ForeignKey("plants.id", ondelete="SET NULL"), nullable=True, index=True)

    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(50), nullable=True)  # watering, harvest, inspection, planting, soil
    task_date = Column(Date, nullable=False, index=True)

    is_completed = Column(Boolean, default=False, nullable=False, index=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    result_notes = Column(Text, nullable=True)  # Observations / results recorded upon task completion
    source = Column(String(50), default="ai_generated", nullable=False)  # ai_generated or user_created

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    garden = relationship("Garden", back_populates="tasks")
    plant = relationship("Plant", back_populates="tasks")

    def __repr__(self) -> str:
        return f"<GardenTask(id={self.id}, title='{self.title}', completed={self.is_completed})>"

