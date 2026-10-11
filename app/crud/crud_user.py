from typing import List, Optional
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserCreate


class CRUDUser:
    """Data access methods for User entity."""

    def get(self, db: Session, user_id: int) -> Optional[User]:
        return db.query(User).filter(User.id == user_id).first()

    def get_by_username(self, db: Session, username: str) -> Optional[User]:
        return db.query(User).filter(User.username == username).first()

    def get_by_email(self, db: Session, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email).first()

    def list(self, db: Session, skip: int = 0, limit: int = 100) -> List[User]:
        return db.query(User).offset(skip).limit(limit).all()

    def create(self, db: Session, user_in: UserCreate) -> User:
        db_user = User(
            username=user_in.username,
            email=user_in.email
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user


user_crud = CRUDUser()

