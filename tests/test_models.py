import os
import pytest
from sqlmodel import SQLModel, Session, create_engine
from app.models.user import User
from app.models.glucose_reading import GlucoseReading
from app.models.meal import Meal
from app.models.meal_ingredient import MealIngredient
from app.models.insulin_dose import InsulinDose
from app.models.activity import Activity
from app.models.condition_log import ConditionLog
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

POSTGRES_TEST_URL = os.getenv("SQLALCHEMY_TEST_DATABASE_URI")
if POSTGRES_TEST_URL is None:
    raise RuntimeError("SQLALCHEMY_TEST_DATABASE_URI environment variable must be set for tests.")


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(POSTGRES_TEST_URL, echo=True)
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)

def test_create_user(session):
    user = User(email="test@example.com", name="Test User", username="testuser", hashed_password="fakehashed")
    session.add(user)
    session.commit()
    assert user.id is not None
    assert user.created_at is not None
    assert user.updated_at is not None

def test_create_meal_with_ingredients(session):
    user = User(email="mealuser@example.com", name="Meal User", username="mealuser", hashed_password="fakehashed")
    session.add(user)
    session.commit()
    assert user.id is not None
    meal = Meal(user_id=user.id, timestamp=datetime.now(timezone.utc), description="Lunch", carbs=45.0)
    session.add(meal)
    session.commit()
    assert meal.id is not None
    ingredient = MealIngredient(meal_id=meal.id, name="Chicken", quantity="100g")
    meal.ingredients.append(ingredient)
    session.add(ingredient)
    session.commit()
    assert meal.ingredients[0].name == "Chicken"

def test_create_glucose_reading(session):
    user = User(email="glucose@example.com", name="Glucose User", username="glucoseuser", hashed_password="fakehashed")
    session.add(user)
    session.commit()
    assert user.id is not None
    reading = GlucoseReading(user_id=user.id, timestamp=datetime.now(timezone.utc), value=120.5, source="CGM")
    session.add(reading)
    session.commit()
    assert reading.id is not None
    assert reading.value == 120.5

def test_create_insulin_dose(session):
    user = User(email="insulin@example.com", name="Insulin User", username="insulinuser", hashed_password="fakehashed")
    session.add(user)
    session.commit()
    assert user.id is not None
    dose = InsulinDose(user_id=user.id, timestamp=datetime.now(timezone.utc), units=5.0, type="Rapid")
    session.add(dose)
    session.commit()
    assert dose.id is not None
    assert dose.units == 5.0

def test_create_activity(session):
    user = User(email="activity@example.com", name="Activity User", username="activityuser", hashed_password="fakehashed")
    session.add(user)
    session.commit()
    assert user.id is not None
    activity = Activity(user_id=user.id, type="Running", intensity="High", duration_min=30, timestamp=datetime.now(timezone.utc))
    session.add(activity)
    session.commit()
    assert activity.id is not None
    assert activity.type == "Running"

def test_create_condition_log(session):
    user = User(email="condition@example.com", name="Condition User", username="conditionuser", hashed_password="fakehashed")
    session.add(user)
    session.commit()
    assert user.id is not None
    log = ConditionLog(user_id=user.id, type="Stress", value="High", timestamp=datetime.now(timezone.utc))
    session.add(log)
    session.commit()
    assert log.id is not None
    assert log.type == "Stress" 