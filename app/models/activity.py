from typing import Optional, TYPE_CHECKING
from sqlmodel import Field, Relationship
from app.models.base import Base
from datetime import datetime

class Activity(Base, table=True):
    __tablename__: str = 'activities'
    user_id: int = Field(foreign_key="users.id")
    type: str
    intensity: Optional[str] = None
    duration_min: Optional[int] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    timestamp: Optional[datetime] = None  
    note: Optional[str] = None
    calories_burned: Optional[float] = None

    user: "User" = Relationship(back_populates="activities")

if TYPE_CHECKING:
    from .user import User 