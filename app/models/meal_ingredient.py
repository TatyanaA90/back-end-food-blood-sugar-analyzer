from typing import Optional, TYPE_CHECKING
from sqlmodel import Field, Relationship
from app.models.base import Base

class MealIngredient(Base, table=True):
    __tablename__: str = 'meal_ingredients'
    meal_id: int = Field(foreign_key="meals.id")
    name: str
    quantity: Optional[str] = None

    meal: "Meal" = Relationship(back_populates="ingredients")

if TYPE_CHECKING:
    from .meal import Meal 