from typing import Optional, TYPE_CHECKING
from sqlmodel import Field, Relationship
from app.models.base import Base

class PredefinedMealIngredient(Base, table=True):
    __tablename__: str = 'predefined_meal_ingredients'
    predefined_meal_id: int = Field(foreign_key="predefined_meals.id")
    name: str
    base_weight: float  # base weight in grams for 1 portion
    carbs_per_100g: float  # carbs per 100g of this ingredient
    glycemic_index: Optional[float] = None
    note: Optional[str] = None

    predefined_meal: "PredefinedMeal" = Relationship(back_populates="ingredients")

if TYPE_CHECKING:
    from .predefined_meal import PredefinedMeal
