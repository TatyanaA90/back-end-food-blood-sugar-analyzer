from sqlmodel import Session, select, delete
from app.models.user import User
from app.models.glucose_reading import GlucoseReading
from app.models.meal import Meal
from app.models.meal_ingredient import MealIngredient
from app.models.insulin_dose import InsulinDose
from app.models.activity import Activity
from app.models.condition_log import ConditionLog
from app.core.security import get_password_hash, verify_password, create_access_token
from app.schemas.admin import (
    AdminStats, UserDetail, AdminUserUpdate, 
    GlucoseReadingData, MealData, ActivityData, 
    InsulinDoseData, ConditionLogData, UserDataResponse
)
from datetime import timedelta
from typing import List, Dict, Any, Optional
from fastapi import HTTPException

class AdminService:
    """Service class for admin-specific operations."""
    
    @staticmethod
    def authenticate_admin(username: str, password: str, session: Session) -> Dict[str, Any]:
        """
        Authenticate admin user with enhanced security validation.
        """
        user = session.exec(select(User).where(User.username == username)).first()
        
        if not user:
            raise HTTPException(status_code=401, detail="Invalid admin credentials")
        
        if not verify_password(password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Invalid admin credentials")
        
        if not user.is_admin:
            raise HTTPException(status_code=403, detail="Insufficient privileges. Admin access required.")
        
        # Create admin-specific token with extended expiration
        access_token = create_access_token(
            data={"sub": user.username},
            expires_delta=timedelta(hours=2),  # Longer session for admin
            is_admin=True
        )
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "username": user.username,
                "is_admin": user.is_admin,
                "weight": user.weight,
                "weight_unit": user.weight_unit
            }
        }
    
    @staticmethod
    def get_system_stats(session: Session) -> AdminStats:
        """
        Get comprehensive system statistics for admin dashboard.
        """
        total_users = len(session.exec(select(User)).all())
        admin_users = len(session.exec(select(User).where(User.is_admin == True)).all())
        regular_users = total_users - admin_users
        
        total_glucose_readings = len(session.exec(select(GlucoseReading)).all())
        total_meals = len(session.exec(select(Meal)).all())
        total_activities = len(session.exec(select(Activity)).all())
        total_insulin_doses = len(session.exec(select(InsulinDose)).all())
        total_condition_logs = len(session.exec(select(ConditionLog)).all())
        
        return AdminStats(
            total_users=total_users,
            total_glucose_readings=total_glucose_readings,
            total_meals=total_meals,
            total_activities=total_activities,
            total_insulin_doses=total_insulin_doses,
            total_condition_logs=total_condition_logs,
            admin_users_count=admin_users,
            regular_users_count=regular_users
        )
    
    @staticmethod
    def get_all_users_detailed(session: Session) -> List[UserDetail]:
        """
        Get detailed information about all users including their data counts.
        """
        users = session.exec(select(User)).all()
        user_details = []
        
        for user in users:
            # Count user's data
            glucose_count = len(session.exec(select(GlucoseReading).where(GlucoseReading.user_id == user.id)).all())
            meals_count = len(session.exec(select(Meal).where(Meal.user_id == user.id)).all())
            activities_count = len(session.exec(select(Activity).where(Activity.user_id == user.id)).all())
            insulin_count = len(session.exec(select(InsulinDose).where(InsulinDose.user_id == user.id)).all())
            logs_count = len(session.exec(select(ConditionLog).where(ConditionLog.user_id == user.id)).all())
            
            user_details.append(UserDetail(
                id=user.id,
                email=user.email,
                name=user.name,
                username=user.username,
                is_admin=user.is_admin,
                weight=user.weight,
                weight_unit=user.weight_unit,
                created_at=user.created_at,
                updated_at=user.updated_at,
                glucose_readings_count=glucose_count,
                meals_count=meals_count,
                activities_count=activities_count,
                insulin_doses_count=insulin_count,
                condition_logs_count=logs_count
            ))
        
        return user_details
    
    @staticmethod
    def get_user_detailed(user_id: int, session: Session) -> UserDetail:
        """
        Get detailed information about a specific user.
        """
        user = session.exec(select(User).where(User.id == user_id)).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Count user's data
        glucose_count = len(session.exec(select(GlucoseReading).where(GlucoseReading.user_id == user.id)).all())
        meals_count = len(session.exec(select(Meal).where(Meal.user_id == user.id)).all())
        activities_count = len(session.exec(select(Activity).where(Activity.user_id == user.id)).all())
        insulin_count = len(session.exec(select(InsulinDose).where(InsulinDose.user_id == user.id)).all())
        logs_count = len(session.exec(select(ConditionLog).where(ConditionLog.user_id == user.id)).all())
        
        return UserDetail(
            id=user.id,
            email=user.email,
            name=user.name,
            username=user.username,
            is_admin=user.is_admin,
            weight=user.weight,
            weight_unit=user.weight_unit,
            created_at=user.created_at,
            updated_at=user.updated_at,
            glucose_readings_count=glucose_count,
            meals_count=meals_count,
            activities_count=activities_count,
            insulin_doses_count=insulin_count,
            condition_logs_count=logs_count
        )
    
    @staticmethod
    def update_user_admin(user_id: int, data: AdminUserUpdate, session: Session) -> Dict[str, Any]:
        """
        Update user information as an admin.
        """
        user = session.exec(select(User).where(User.id == user_id)).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Update fields if provided
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(user, field, value)
        
        session.add(user)
        session.commit()
        session.refresh(user)
        
        return {
            "message": "User updated successfully",
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "username": user.username,
                "is_admin": user.is_admin,
                "weight": user.weight,
                "weight_unit": user.weight_unit
            }
        }
    
    @staticmethod
    def get_user_data(user_id: int, session: Session) -> Dict[str, Any]:
        """
        Get all data associated with a specific user.
        """
        user = session.exec(select(User).where(User.id == user_id)).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get user's data
        glucose_readings = session.exec(select(GlucoseReading).where(GlucoseReading.user_id == user.id)).all()
        meals = session.exec(select(Meal).where(Meal.user_id == user.id)).all()
        activities = session.exec(select(Activity).where(Activity.user_id == user.id)).all()
        insulin_doses = session.exec(select(InsulinDose).where(InsulinDose.user_id == user.id)).all()
        condition_logs = session.exec(select(ConditionLog).where(ConditionLog.user_id == user.id)).all()
        
        return {
            "user": {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "username": user.username,
                "is_admin": user.is_admin,
                "weight": user.weight,
                "weight_unit": user.weight_unit,
                "created_at": user.created_at,
                "updated_at": user.updated_at
            },
            "glucose_readings": [
                GlucoseReadingData(
                    id=reading.id,
                    value=reading.value,
                    unit=reading.unit,
                    timestamp=reading.timestamp,
                    notes=reading.notes
                ) for reading in glucose_readings
            ],
            "meals": [
                MealData(
                    id=meal.id,
                    name=meal.name,
                    meal_type=meal.meal_type,
                    timestamp=meal.timestamp,
                    total_carbs=meal.total_carbs,
                    total_calories=meal.total_calories
                ) for meal in meals
            ],
            "activities": [
                ActivityData(
                    id=activity.id,
                    name=activity.name,
                    activity_type=activity.activity_type,
                    duration_minutes=activity.duration_minutes,
                    calories_burned=activity.calories_burned,
                    timestamp=activity.timestamp
                ) for activity in activities
            ],
            "insulin_doses": [
                InsulinDoseData(
                    id=dose.id,
                    insulin_type=dose.insulin_type,
                    units=dose.units,
                    timestamp=dose.timestamp,
                    notes=dose.notes
                ) for dose in insulin_doses
            ],
            "condition_logs": [
                ConditionLogData(
                    id=log.id,
                    condition_type=log.condition_type,
                    severity=log.severity,
                    notes=log.notes,
                    timestamp=log.timestamp
                ) for log in condition_logs
            ]
        }
    
    @staticmethod
    def reset_user_password(user_id: int, new_password: str, session: Session) -> str:
        """
        Reset a user's password as an admin.
        """
        user = session.exec(select(User).where(User.id == user_id)).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Hash the new password
        user.hashed_password = get_password_hash(new_password)
        session.add(user)
        session.commit()
        
        return f"Password reset successfully for user {user.username}"
    
    @staticmethod
    def delete_user_admin(user_id: int, current_admin_id: int, session: Session) -> str:
        """
        Delete a user and all their associated data.
        """
        user = session.exec(select(User).where(User.id == user_id)).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Prevent admin from deleting themselves
        if user.id == current_admin_id:
            raise HTTPException(status_code=400, detail="Cannot delete your own account")
        
        # Delete all associated data first (due to foreign key constraints)
        session.exec(delete(ConditionLog).where(ConditionLog.user_id == user_id))
        session.exec(delete(Activity).where(Activity.user_id == user_id))
        session.exec(delete(InsulinDose).where(InsulinDose.user_id == user_id))
        session.exec(delete(MealIngredient).where(MealIngredient.meal_id.in_(
            select(Meal.id).where(Meal.user_id == user_id)
        )))
        session.exec(delete(Meal).where(Meal.user_id == user_id))
        session.exec(delete(GlucoseReading).where(GlucoseReading.user_id == user_id))
        
        # Finally delete the user
        session.exec(delete(User).where(User.id == user_id))
        session.commit()
        
        return f"User {user.username} and all associated data deleted successfully"
    
    @staticmethod
    def truncate_all_users(session: Session) -> str:
        """
        Delete ALL users and ALL related data.
        Only use for development/testing purposes.
        """
        try:
            # Delete all related data first (due to foreign key constraints)
            session.exec(delete(ConditionLog))
            session.exec(delete(Activity))
            session.exec(delete(InsulinDose))
            session.exec(delete(MealIngredient))
            session.exec(delete(Meal))
            session.exec(delete(GlucoseReading))
            session.exec(delete(User))
            session.commit()
            
            return "All users and data deleted successfully"
        except Exception as e:
            session.rollback()
            raise HTTPException(status_code=500, detail=f"Error deleting data: {str(e)}") 