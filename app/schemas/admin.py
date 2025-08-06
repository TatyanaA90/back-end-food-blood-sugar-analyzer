from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Dict, Any, List, Optional

# Admin Authentication Schemas
class AdminLoginRequest(BaseModel):
    username: str
    password: str

class AdminLoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: dict
    message: str = "Admin authentication successful"

# Admin User Management Schemas
class AdminPasswordReset(BaseModel):
    user_id: int
    new_password: str

class UserCount(BaseModel):
    total_users: int

class UserDetail(BaseModel):
    id: int
    email: str
    name: str
    username: str
    is_admin: bool
    weight: Optional[float] = None
    weight_unit: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    glucose_readings_count: int = 0
    meals_count: int = 0
    activities_count: int = 0
    insulin_doses_count: int = 0
    condition_logs_count: int = 0

class AdminUserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    weight: Optional[float] = None
    weight_unit: Optional[str] = None
    is_admin: Optional[bool] = None

# Admin Statistics Schemas
class AdminStats(BaseModel):
    total_users: int
    total_glucose_readings: int
    total_meals: int
    total_activities: int
    total_insulin_doses: int
    total_condition_logs: int
    admin_users_count: int
    regular_users_count: int

# Admin Data Schemas
class GlucoseReadingData(BaseModel):
    id: int
    value: float
    unit: str
    timestamp: datetime
    notes: Optional[str] = None

class MealData(BaseModel):
    id: int
    name: str
    meal_type: str
    timestamp: datetime
    total_carbs: Optional[float] = None
    total_calories: Optional[float] = None

class ActivityData(BaseModel):
    id: int
    name: str
    activity_type: str
    duration_minutes: int
    calories_burned: Optional[float] = None
    timestamp: datetime

class InsulinDoseData(BaseModel):
    id: int
    insulin_type: str
    units: float
    timestamp: datetime
    notes: Optional[str] = None

class ConditionLogData(BaseModel):
    id: int
    condition_type: str
    severity: str
    notes: Optional[str] = None
    timestamp: datetime

class UserDataResponse(BaseModel):
    user: Dict[str, Any]
    glucose_readings: List[GlucoseReadingData]
    meals: List[MealData]
    activities: List[ActivityData]
    insulin_doses: List[InsulinDoseData]
    condition_logs: List[ConditionLogData]

# Admin System Management Schemas
class SystemHealth(BaseModel):
    status: str
    database_connected: bool
    total_users: int
    active_sessions: int
    system_uptime: str

class AdminAuditLog(BaseModel):
    id: int
    admin_user_id: int
    admin_username: str
    action: str
    target_user_id: Optional[int] = None
    target_username: Optional[str] = None
    details: Dict[str, Any]
    timestamp: datetime 