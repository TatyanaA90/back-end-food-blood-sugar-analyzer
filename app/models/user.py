from typing import List, Optional, TYPE_CHECKING
from datetime import datetime
from sqlmodel import Field, Relationship
from app.models.base import Base

class User(Base, table=True):
    __tablename__: str = 'users'
    email: str = Field(index=True, unique=True, nullable=False)
    name: str
    username: str = Field(index=True, unique=True, nullable=False)
    hashed_password: str
    is_admin: bool = Field(default=False)
    weight: Optional[float] = None  # Always stored in kg for calculations
    weight_unit: str = Field(default="kg")  # User's preferred unit: "kg" or "lb"
    reset_token: Optional[str] = Field(default=None)
    reset_token_expires: Optional[datetime] = Field(default=None)

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