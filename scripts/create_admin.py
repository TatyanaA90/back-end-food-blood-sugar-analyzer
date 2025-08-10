import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlmodel import Session, select
from app.core.database import get_session
from app.core.security import get_password_hash

# Ensure all models are imported so SQLModel/SQLAlchemy can resolve relationships
from app.models.user import User
from app.models.meal import Meal
from app.models.meal_ingredient import MealIngredient
from app.models.glucose_reading import GlucoseReading
from app.models.insulin_dose import InsulinDose
from app.models.activity import Activity
from app.models.condition_log import ConditionLog
from app.models.predefined_meal import PredefinedMeal
from app.models.predefined_meal_ingredient import PredefinedMealIngredient

def create_admin_user(
    email: str,
    username: str,
    name: str,
    password: str,
    session: Session
) -> User:
    # Check if user already exists
    existing_user = session.exec(
        select(User).where(
            (User.email == email) | (User.username == username)
        )
    ).first()

    if existing_user:
        print(f"User with email {email} or username {username} already exists")
        return existing_user

    # Create new admin user
    admin_user = User(
        email=email,
        username=username,
        name=name,
        hashed_password=get_password_hash(password),
        is_admin=True
    )

    session.add(admin_user)
    session.commit()
    session.refresh(admin_user)

    print(f"Created admin user: {username}")
    return admin_user

if __name__ == "__main__":
    # Get database session
    session = next(get_session())

    # Create admin user
    admin = create_admin_user(
        email="admin@example.com",
        username="admin",
        name="Admin User",
        password="Admin123!",  # Change this!
        session=session
    )