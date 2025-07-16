from typing import List, Optional, TYPE_CHECKING
from sqlmodel import Field, Relationship
from app.models.base import Base
from datetime import datetime

class Meal(Base, table=True):
    __tablename__: str = 'meals'
    user_id: int = Field(foreign_key="users.id")
    timestamp: Optional[datetime] = None
    description: Optional[str] = None
    carbs: Optional[float] = None
    photo_url: Optional[str] = None

    user: "User" = Relationship(back_populates="meals")
    ingredients: List["MealIngredient"] = Relationship(back_populates="meal")
    insulin_doses: List["InsulinDose"] = Relationship(back_populates="related_meal")

if TYPE_CHECKING:
    from .user import User
    from .meal_ingredient import MealIngredient
    from .insulin_dose import InsulinDose 