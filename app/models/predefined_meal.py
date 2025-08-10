from typing import List, Optional, TYPE_CHECKING
from sqlmodel import Field, Relationship
from app.models.base import Base

class PredefinedMeal(Base, table=True):
    __tablename__: str = 'predefined_meals'
    name: str
    description: Optional[str] = None
    category: Optional[str] = None  # breakfast, lunch, dinner, snack, dessert, beverage
    is_active: bool = Field(default=True)
    created_by_admin: bool = Field(default=True)
    owner_user_id: Optional[int] = Field(default=None, foreign_key="users.id")

    ingredients: List["PredefinedMealIngredient"] = Relationship(back_populates="predefined_meal")
    user_meals: List["Meal"] = Relationship(back_populates="predefined_meal")
    if TYPE_CHECKING:
        from .user import User  # noqa: F401

if TYPE_CHECKING:
    from .predefined_meal_ingredient import PredefinedMealIngredient
    from .meal import Meal
