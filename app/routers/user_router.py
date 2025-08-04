from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, delete
from app.core.database import get_session
from app.models.user import User
from app.models.glucose_reading import GlucoseReading
from app.models.meal import Meal
from app.models.meal_ingredient import MealIngredient
from app.models.insulin_dose import InsulinDose
from app.models.activity import Activity
from app.models.condition_log import ConditionLog
from pydantic import BaseModel
from app.core.security import get_password_hash, verify_password, create_access_token, get_current_user
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from sqlalchemy.exc import IntegrityError

router = APIRouter()

class UserCreate(BaseModel):
    email: str
    name: str
    username: str
    password: str

class UserRead(BaseModel):
    id: int
    email: str
    name: str
    username: str

class UserRegistrationResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserRead

@router.post("/users", response_model=UserRegistrationResponse)
def create_user(user: UserCreate, session: Session = Depends(get_session)):
    """Create a new user account with hashed password for secure storage."""
    try:
        db_user = User(
            email=user.email,
            name=user.name,
            username=user.username,
            hashed_password=get_password_hash(user.password)
        )
        session.add(db_user)
        session.commit()
        session.refresh(db_user)
        
        # Create access token for immediate login after registration
        access_token = create_access_token(
            data={"sub": db_user.username},
            expires_delta=timedelta(minutes=30)
        )
        
        return UserRegistrationResponse(
            access_token=access_token,
            token_type="bearer",
            user=UserRead(
                id=db_user.id,
                email=db_user.email,
                name=db_user.name,
                username=db_user.username
            )
        )
    except IntegrityError:
        session.rollback()
        raise HTTPException(
            status_code=409,
            detail="Username or email already exists"
        )

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class UserLoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserRead

@router.options("/login")
def login_options():
    """Handle CORS preflight requests for the login endpoint."""
    return {"message": "CORS preflight OK"}

@router.post("/login", response_model=UserLoginResponse)
def login(user_login: UserLogin, session: Session = Depends(get_session)):
    """Authenticate user credentials and return JWT access token for session management."""
    user = session.exec(select(User).where(User.username == user_login.username)).first()
    if not user or not verify_password(user_login.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=30)
    )
    return UserLoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserRead(
            id=user.id,
            email=user.email,
            name=user.name,
            username=user.username
        )
    )

@router.get("/users/{user_id}", response_model=UserRead)
def get_user(user_id: int, session: Session = Depends(get_session)):
    """Retrieve user information by user ID from the database."""
    user = session.exec(select(User).where(User.id == user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.get("/users", response_model=list[UserRead])
def get_all_users(session: Session = Depends(get_session)):
    """Retrieve all users from the database for administrative purposes."""
    users = session.exec(select(User)).all()
    return users

@router.get("/me", response_model=UserRead)
def read_me(current_user: User = Depends(get_current_user)):
    """Get the currently authenticated user's information."""
    return current_user

@router.delete("/users/truncate-all")
def truncate_all_users(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    ⚠️ DANGER: Delete ALL users and ALL related data.
    Only use for development/testing purposes.
    Requires admin privileges.
    """
    # Check if current user is admin
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        # Delete all related data first (due to foreign key constraints)
        session.exec(delete(ConditionLog))
        session.exec(delete(Activity))
        session.exec(delete(InsulinDose))
        session.exec(delete(MealIngredient))
        session.exec(delete(Meal))
        session.exec(delete(GlucoseReading))
        
        # Finally delete all users
        result = session.exec(delete(User))
        users_deleted = result.rowcount
        
        session.commit()
        
        return {
            "message": f"Successfully deleted {users_deleted} users and all related data",
            "users_deleted": users_deleted,
            "warning": "All user data has been permanently deleted"
        }
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error truncating data: {str(e)}")

@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a specific user and all their related data.
    Users can delete their own account, or admins can delete any user.
    """
    # Check if current user is admin or deleting their own account
    if not current_user.is_admin and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="You can only delete your own account, or be an admin")
    
    # Find the user
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prevent admin from deleting themselves (safety measure)
    if current_user.id == user_id and current_user.is_admin:
        # Check if there are other admins
        other_admins = session.exec(
            select(User).where(User.is_admin == True, User.id != user_id)
        ).all()
        if not other_admins:
            raise HTTPException(
                status_code=400, 
                detail="Cannot delete the last admin account. Create another admin first."
            )
    
    try:
        # Delete related data first (foreign key constraints)
        session.exec(delete(ConditionLog).where(ConditionLog.user_id == user_id))
        session.exec(delete(Activity).where(Activity.user_id == user_id))
        session.exec(delete(InsulinDose).where(InsulinDose.user_id == user_id))
        
        # Delete meal ingredients for user's meals
        user_meals = session.exec(select(Meal.id).where(Meal.user_id == user_id)).all()
        for meal_id in user_meals:
            session.exec(delete(MealIngredient).where(MealIngredient.meal_id == meal_id))
        
        session.exec(delete(Meal).where(Meal.user_id == user_id))
        session.exec(delete(GlucoseReading).where(GlucoseReading.user_id == user_id))
        
        # Finally delete the user
        session.delete(user)
        session.commit()
        
        return {
            "message": f"Successfully deleted user '{user.username}' and all related data",
            "deleted_user": user.username
        }
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting user: {str(e)}")

@router.get("/users/count")
def get_users_count(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get total number of users in the database (admin only)."""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    users_count = len(session.exec(select(User)).all())
    return {"total_users": users_count} 