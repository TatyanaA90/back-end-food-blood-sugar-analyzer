from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel

# MealIngredient Schemas
class MealIngredientBase(BaseModel):
    name: str
    weight: Optional[float] = None  # in grams
    carbs: float
    glycemic_index: Optional[float] = None
    note: Optional[str] = None

class MealIngredientCreate(MealIngredientBase):
    pass

class MealIngredientUpdate(MealIngredientBase):
    pass

class MealIngredientRead(MealIngredientBase):
    id: int
    class Config:
        orm_mode = True

# Meal Schemas
class MealBase(BaseModel):
    description: Optional[str] = None
    total_weight: Optional[float] = None
    total_carbs: Optional[float] = None
    glycemic_index: Optional[float] = None
    note: Optional[str] = None
    photo_url: Optional[str] = None
    timestamp: Optional[datetime] = None

class MealCreate(MealBase):
    ingredients: List[MealIngredientCreate]

class MealUpdate(MealBase):
    ingredients: Optional[List[MealIngredientCreate]] = None

class MealReadBasic(MealBase):
    id: int
    class Config:
        orm_mode = True

class MealReadDetail(MealReadBasic):
    ingredients: List[MealIngredientRead]
