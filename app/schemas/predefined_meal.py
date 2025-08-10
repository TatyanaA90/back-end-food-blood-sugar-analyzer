from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime

# Predefined Meal Ingredient Schemas
class PredefinedMealIngredientBase(BaseModel):
    name: str
    base_weight: float  # base weight in grams for 1 portion
    carbs_per_100g: float  # carbs per 100g of this ingredient
    glycemic_index: Optional[float] = None
    note: Optional[str] = None

class PredefinedMealIngredientCreate(PredefinedMealIngredientBase):
    pass

class PredefinedMealIngredientUpdate(PredefinedMealIngredientBase):
    pass

class PredefinedMealIngredientRead(PredefinedMealIngredientBase):
    id: int
    predefined_meal_id: int
    model_config = ConfigDict(from_attributes=True)

# Predefined Meal Schemas
class PredefinedMealBase(BaseModel):
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    is_active: bool = True
    created_by_admin: bool = True

class PredefinedMealCreate(PredefinedMealBase):
    ingredients: List[PredefinedMealIngredientCreate]

class PredefinedMealUpdate(PredefinedMealBase):
    ingredients: Optional[List[PredefinedMealIngredientCreate]] = None

class PredefinedMealRead(PredefinedMealBase):
    id: int
    # personal templates have owner_user_id; admin templates have None
    # we expose for admin tooling if needed in UI, safe to keep optional
    # owner_user_id omitted in create/update inputs
    # owner_user_id: Optional[int] = None  # keep internal if desired
    ingredients: List[PredefinedMealIngredientRead]
    model_config = ConfigDict(from_attributes=True)

# Meal creation from predefined template
class MealFromPredefinedCreate(BaseModel):
    predefined_meal_id: int
    quantity: int = 1  # number of portions (1-10)
    timestamp: Optional[datetime] = None
    note: Optional[str] = None
    photo_url: Optional[str] = None
    ingredient_adjustments: Optional[List[dict]] = None  # List of {ingredient_id, adjusted_weight}

# Response schemas
class PredefinedMealWithNutrition(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    ingredients: List[PredefinedMealIngredientRead]
    total_carbs_per_portion: float
    total_weight_per_portion: float
    average_glycemic_index: Optional[float] = None
    created_by_admin: bool
    owner_user_id: Optional[int] = None
    model_config = ConfigDict(from_attributes=True)
