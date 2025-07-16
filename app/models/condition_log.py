from typing import Optional, TYPE_CHECKING
from sqlmodel import Field, Relationship
from app.models.base import Base
from datetime import datetime

class ConditionLog(Base, table=True):
    __tablename__: str ='condition_logs'
    user_id: int = Field(foreign_key="users.id")
    type: str
    value: Optional[str] = None
    timestamp: Optional[datetime] = None

    user: "User" = Relationship(back_populates="condition_logs")

if TYPE_CHECKING:
    from .user import User 