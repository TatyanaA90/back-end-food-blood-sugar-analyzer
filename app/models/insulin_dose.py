from typing import Optional, TYPE_CHECKING
from sqlmodel import Field, Relationship
from app.models.base import Base
from datetime import datetime

class InsulinDose(Base, table=True):
    __tablename__: str = 'insulin_doses'
    user_id: int = Field(foreign_key="users.id")
    timestamp: Optional[datetime] = None
    units: float
    type: Optional[str] = None
    meal_context: Optional[str] = None  # Breakfast, Lunch, Dinner, Snack, Dessert, Beverage, Other
    note: Optional[str] = None
    related_meal_id: Optional[int] = Field(default=None, foreign_key="meals.id")

    user: "User" = Relationship(back_populates="insulin_doses")
    related_meal: Optional["Meal"] = Relationship(back_populates="insulin_doses")

if TYPE_CHECKING:
    from .user import User
    from .meal import Meal 