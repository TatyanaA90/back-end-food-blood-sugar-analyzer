from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict

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
    model_config = ConfigDict(from_attributes=True)

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
    model_config = ConfigDict(from_attributes=True)

class MealReadDetail(MealReadBasic):
    ingredients: List[MealIngredientRead]

# Activity Schemas
class ActivityBase(BaseModel):
    type: str
    intensity: Optional[str] = None
    duration_min: Optional[int] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    timestamp: Optional[datetime] = None 
    note: Optional[str] = None

class ActivityCreate(ActivityBase):
    pass

class ActivityUpdate(ActivityBase):
    pass

class ActivityReadBasic(ActivityBase):
    id: int
    calories_burned: Optional[float] = None
    model_config = ConfigDict(from_attributes=True)

class ActivityReadDetail(ActivityReadBasic):
    pass

# ConditionLog Schemas
class ConditionLogBase(BaseModel):
    type: str
    value: Optional[str] = None
    timestamp: Optional[datetime] = None
    note: Optional[str] = None

class ConditionLogCreate(ConditionLogBase):
    pass

class ConditionLogUpdate(ConditionLogBase):
    pass

class ConditionLogReadBasic(ConditionLogBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class ConditionLogReadDetail(ConditionLogReadBasic):
    pass

# InsulinDose Schemas
class InsulinDoseBase(BaseModel):
    units: float
    timestamp: Optional[datetime] = None
    note: Optional[str] = None

class InsulinDoseCreate(InsulinDoseBase):
    pass

class InsulinDoseUpdate(InsulinDoseBase):
    pass

class InsulinDoseReadBasic(InsulinDoseBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class InsulinDoseReadDetail(InsulinDoseReadBasic):
    pass

# GlucoseReading Schemas
class GlucoseReadingBase(BaseModel):
    value: float
    unit: str = "mg/dl"  # "mg/dl" or "mmol/l"
    timestamp: Optional[datetime] = None
    note: Optional[str] = None

class GlucoseReadingCreate(GlucoseReadingBase):
    pass

class GlucoseReadingUpdate(GlucoseReadingBase):
    pass

class GlucoseReadingReadBasic(GlucoseReadingBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class GlucoseReadingReadDetail(GlucoseReadingReadBasic):
    pass
