from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.core.database import get_session
from app.models.user import User
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

@router.options("/login")
def login_options():
    """Handle CORS preflight requests for the login endpoint."""
    return {"message": "CORS preflight OK"}

@router.post("/login", response_model=Token)
def login(user_login: UserLogin, session: Session = Depends(get_session)):
    """Authenticate user credentials and return JWT access token for session management."""
    user = session.exec(select(User).where(User.username == user_login.username)).first()
    if not user or not verify_password(user_login.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=30)
    )
    return {"access_token": access_token, "token_type": "bearer"}

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