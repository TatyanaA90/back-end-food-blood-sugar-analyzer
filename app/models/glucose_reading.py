from typing import Optional, TYPE_CHECKING
from sqlmodel import Field, Relationship
from app.models.base import Base
from datetime import datetime

class GlucoseReading(Base, table=True):
    __tablename__: str ='glucose_readings'
    user_id: int = Field(foreign_key="users.id")
    timestamp: Optional[datetime] = None
    value: float
    source: Optional[str] = None

    user: "User" = Relationship(back_populates="glucose_readings")

if TYPE_CHECKING:
    from .user import User 