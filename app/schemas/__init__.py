# Schemas package - Import all schemas
from ..schemas_legacy import (
    # Meal schemas
    MealBase, MealCreate, MealUpdate, MealReadBasic, MealReadDetail,
    # MealIngredient schemas
    MealIngredientBase, MealIngredientCreate, MealIngredientUpdate, MealIngredientRead,
    # Activity schemas
    ActivityBase, ActivityCreate, ActivityUpdate, ActivityReadBasic, ActivityReadDetail,
    # ConditionLog schemas
    ConditionLogBase, ConditionLogCreate, ConditionLogUpdate, ConditionLogReadBasic, ConditionLogReadDetail,
    # InsulinDose schemas
    InsulinDoseBase, InsulinDoseCreate, InsulinDoseUpdate, InsulinDoseReadBasic, InsulinDoseReadDetail,
    # GlucoseReading schemas
    GlucoseReadingBase, GlucoseReadingCreate, GlucoseReadingUpdate, GlucoseReadingReadBasic, GlucoseReadingReadDetail
)

# Import admin schemas
from .admin import (
    AdminLoginRequest, AdminLoginResponse, AdminPasswordReset,
    UserCount, UserDetail, AdminUserUpdate, AdminStats,
    GlucoseReadingData, MealData, ActivityData, InsulinDoseData, ConditionLogData, UserDataResponse,
    SystemHealth, AdminAuditLog
) 