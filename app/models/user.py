from typing import List, TYPE_CHECKING
from sqlmodel import Field, Relationship
from app.models.base import Base

class User(Base, table=True):
    __tablename__: str = 'users'
    email: str = Field(index=True, unique=True, nullable=False)
    name: str
    username: str = Field(index=True, unique=True, nullable=False)
    hashed_password: str

    glucose_readings: List["GlucoseReading"] = Relationship(back_populates="user")
    meals: List["Meal"] = Relationship(back_populates="user")
    insulin_doses: List["InsulinDose"] = Relationship(back_populates="user")
    activities: List["Activity"] = Relationship(back_populates="user")
    condition_logs: List["ConditionLog"] = Relationship(back_populates="user")

if TYPE_CHECKING:
    from .glucose_reading import GlucoseReading
    from .meal import Meal
    from .insulin_dose import InsulinDose
    from .activity import Activity
    from .condition_log import ConditionLog 