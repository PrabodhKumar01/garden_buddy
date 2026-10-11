from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Garden(Base):
    """Garden entity representing a user's garden plot or space."""

    __tablename__ = "gardens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(150), nullable=False)
    location = Column(String(255), nullable=True)  # City or geographic location for weather queries
    garden_type = Column(String(100), nullable=True)  # e.g., Backyard, Balcony, Container, Raised Bed
    sunlight = Column(String(100), nullable=True)  # e.g., Full Sun, Partial Shade, Full Shade
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="gardens")
    plants = relationship("Plant", back_populates="garden", cascade="all, delete-orphan")
    tasks = relationship("GardenTask", back_populates="garden", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Garden(id={self.id}, name='{self.name}', location='{self.location}')>"

