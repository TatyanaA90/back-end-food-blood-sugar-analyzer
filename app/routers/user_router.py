from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select, delete
from app.core.database import get_session
from app.models.user import User
from app.models.glucose_reading import GlucoseReading
from app.models.meal import Meal
from app.models.meal_ingredient import MealIngredient
from app.models.insulin_dose import InsulinDose
from app.models.activity import Activity
from app.models.condition_log import ConditionLog
from pydantic import BaseModel, EmailStr
from app.core.security import get_password_hash, verify_password, create_access_token, get_current_user, get_current_admin_user
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta, datetime, UTC
from sqlalchemy.exc import IntegrityError
import secrets
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings

router = APIRouter()

class UserCreate(BaseModel):
    email: str
    name: str
    username: str
    password: str
    weight: float | None = None
    weight_unit: str | None = None

class UserRead(BaseModel):
    id: int
    email: str
    name: str
    username: str
    is_admin: bool
    weight: float | None = None
    weight_unit: str | None = None

class UserRegistrationResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserRead

class PasswordChange(BaseModel):
    current_password: str
    new_password: str

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordReset(BaseModel):
    token: str
    new_password: str

class UserUpdateData(BaseModel):
    name: str | None = None
    email: str | None = None
    weight: float | None = None
    weight_unit: str | None = None

class AdminPasswordReset(BaseModel):
    user_id: int
    new_password: str

class UserCount(BaseModel):
    total_users: int

def send_reset_email(email: str, reset_token: str):
    """Send password reset email to user."""
    try:
        msg = MIMEMultipart()
        msg['From'] = settings.SMTP_SENDER
        msg['To'] = email
        msg['Subject'] = "Password Reset Request"

        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
        body = f"""
        You have requested to reset your password.
        
        Click the link below to reset your password:
        {reset_url}
        
        If you did not request this, please ignore this email.
        The link will expire in 1 hour.
        """
        
        msg.attach(MIMEText(body, 'plain'))

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            if settings.SMTP_TLS:
                server.starttls()
            if settings.SMTP_USER and settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)
            
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

@router.post("/forgot-password")
def forgot_password(request: PasswordResetRequest, session: Session = Depends(get_session)):
    """Request a password reset token."""
    user = session.exec(select(User).where(User.email == request.email)).first()
    if not user:
        # Don't reveal if email exists
        return {"message": "If an account exists with this email, a reset link will be sent."}
    
    # Generate reset token
    reset_token = secrets.token_urlsafe(32)
    user.reset_token = reset_token
    user.reset_token_expires = datetime.now(UTC) + timedelta(hours=1)
    
    session.add(user)
    session.commit()
    
    # Send reset email
    if send_reset_email(request.email, reset_token):
        return {"message": "If an account exists with this email, a reset link will be sent."}
    else:
        # For testing, we'll return success even if email fails
        return {"message": "If an account exists with this email, a reset link will be sent."}

@router.post("/reset-password")
def reset_password(reset_data: PasswordReset, session: Session = Depends(get_session)):
    """Reset password using reset token."""
    user = session.exec(select(User).where(User.reset_token == reset_data.token)).first()
    
    if not user or not user.reset_token_expires or user.reset_token_expires < datetime.now(UTC):
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    
    # Update password
    user.hashed_password = get_password_hash(reset_data.new_password)
    user.reset_token = None
    user.reset_token_expires = None
    
    session.add(user)
    session.commit()
    
    return {"message": "Password reset successfully"}

@router.post("/me/change-password")
def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Change the current user's password."""
    # Verify current password
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(status_code=401, detail="Current password is incorrect")
    
    # Hash and update new password
    current_user.hashed_password = get_password_hash(password_data.new_password)
    session.add(current_user)
    session.commit()
    
    return {"message": "Password changed successfully"}

@router.post("/users", response_model=UserRegistrationResponse)
def create_user(user: UserCreate, session: Session = Depends(get_session)):
    """Create a new user account with hashed password for secure storage."""
    try:
        db_user = User(
            email=user.email,
            name=user.name,
            username=user.username,
            hashed_password=get_password_hash(user.password),
            weight=user.weight,
            weight_unit=user.weight_unit
        )
        session.add(db_user)
        session.commit()
        session.refresh(db_user)
        
        # Create access token for immediate login after registration
        access_token = create_access_token(
            data={"sub": db_user.username},
            expires_delta=timedelta(minutes=30),
            is_admin=db_user.is_admin
        )
        
        return UserRegistrationResponse(
            access_token=access_token,
            token_type="bearer",
            user=UserRead(
                id=db_user.id,
                email=db_user.email,
                name=db_user.name,
                username=db_user.username,
                is_admin=db_user.is_admin,
                weight=db_user.weight,
                weight_unit=db_user.weight_unit
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
        expires_delta=timedelta(minutes=30),
        is_admin=user.is_admin
    )
    return UserLoginResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserRead(
            id=user.id,
            email=user.email,
            name=user.name,
            username=user.username,
            is_admin=user.is_admin,
            weight=user.weight,
            weight_unit=user.weight_unit
        )
    )

@router.get("/users/stats/count", response_model=UserCount)
def get_users_count(
    current_user: User = Depends(get_current_admin_user),
    session: Session = Depends(get_session)
):
    """Get total number of users in the database (admin only)."""
    users_count = len(session.exec(select(User)).all())
    return UserCount(total_users=users_count)

@router.get("/users", response_model=list[UserRead])
def get_all_users(session: Session = Depends(get_session)):
    """Retrieve all users from the database for administrative purposes."""
    users = session.exec(select(User)).all()
    return users

@router.get("/users/{user_id}", response_model=UserRead)
def get_user(user_id: int, session: Session = Depends(get_session)):
    """Retrieve user information by user ID from the database."""
    user = session.exec(select(User).where(User.id == user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.get("/me", response_model=UserRead)
def read_me(current_user: User = Depends(get_current_user)):
    """Get the currently authenticated user's information."""
    return current_user

@router.put("/me", response_model=UserRead)
def update_me(
    data: UserUpdateData,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Update current user's profile."""
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(current_user, field, value)
    
    session.add(current_user)
    session.commit()
    session.refresh(current_user)
    
    return current_user

@router.delete("/users/truncate-all")
def truncate_all_users(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_admin_user)
):
    """
    ⚠️ DANGER: Delete ALL users and ALL related data.
    Only use for development/testing purposes.
    Requires admin privileges.
    """
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

@router.post("/admin/reset-password")
def admin_reset_password(
    reset_data: AdminPasswordReset,
    current_user: User = Depends(get_current_admin_user),
    session: Session = Depends(get_session)
):
    """Reset a user's password (admin only)."""
    user = session.get(User, reset_data.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.hashed_password = get_password_hash(reset_data.new_password)
    session.add(user)
    session.commit()
    
    return {"message": "Password reset successfully"}

@router.get("/users/count", response_model=UserCount)
def get_users_count(
    current_user: User = Depends(get_current_admin_user),
    session: Session = Depends(get_session)
):
    """Get total number of users in the database (admin only)."""
    users_count = len(session.exec(select(User)).all())
    return UserCount(total_users=users_count)