from typing import List, Optional, TYPE_CHECKING
from sqlmodel import Field, Relationship
from app.models.base import Base
from datetime import datetime

class Meal(Base, table=True):
    __tablename__: str = 'meals'
    user_id: int = Field(foreign_key="users.id")
    timestamp: Optional[datetime] = None
    description: Optional[str] = None
    meal_type: Optional[str] = None  # Breakfast, Lunch, Dinner, Snack, Dessert, Beverage
    total_weight: Optional[float] = None  # sum of ingredient weights
    total_carbs: Optional[float] = None   # sum of ingredient carbs
    glycemic_index: Optional[float] = None
    note: Optional[str] = None
    photo_url: Optional[str] = None
    
    # Predefined meal support
    is_predefined: bool = Field(default=False)
    predefined_meal_id: Optional[int] = Field(default=None, foreign_key="predefined_meals.id")
    quantity: Optional[int] = Field(default=1)  # number of portions (1-10)

    user: "User" = Relationship(back_populates="meals")
    ingredients: List["MealIngredient"] = Relationship(back_populates="meal")
    insulin_doses: List["InsulinDose"] = Relationship(back_populates="related_meal")
    predefined_meal: Optional["PredefinedMeal"] = Relationship(back_populates="user_meals")

if TYPE_CHECKING:
    from .user import User
    from .meal_ingredient import MealIngredient
    from .insulin_dose import InsulinDose
    from .predefined_meal import PredefinedMeal 