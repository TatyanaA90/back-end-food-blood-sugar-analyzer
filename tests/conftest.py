import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy.pool import StaticPool
from app.core.database import get_session
from app.core.config import settings
from app.main import app

from app.models.user import User
from app.models.glucose_reading import GlucoseReading
from app.models.meal import Meal
from app.models.meal_ingredient import MealIngredient
from app.models.insulin_dose import InsulinDose
from app.models.activity import Activity
from app.models.condition_log import ConditionLog
from app.models.predefined_meal import PredefinedMeal
from app.models.predefined_meal_ingredient import PredefinedMealIngredient

# =============================================================================
# IMPORT COMMON FUNCTIONS NEEDED IN TESTS
# =============================================================================
from app.core.security import get_password_hash, create_access_token

@pytest.fixture(scope="session")
def test_engine():
    """Create a test database engine"""
    # Use in-memory SQLite for tests
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    # This will create ALL tables because models are imported above
    SQLModel.metadata.create_all(engine)
    return engine

@pytest.fixture
def session(test_engine):
    """Create a new database session for a test"""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def client(session):
    """Create a test client with a test database session"""
    def get_test_session():
        yield session

    app.dependency_overrides[get_session] = get_test_session
    yield TestClient(app)
    app.dependency_overrides.clear()

# =============================================================================
# COMMON TEST FIXTURES
# =============================================================================
@pytest.fixture
def test_user(session):
    """Create a test user and return their data"""
    import uuid

    unique_id = str(uuid.uuid4())[:8]
    user_data = {
        "email": f"test{unique_id}@example.com",
        "username": f"testuser{unique_id}",
        "password": "TestPass123!",
        "name": "Test User"
    }

    db_user = User(
        email=user_data["email"],
        username=user_data["username"],
        name=user_data["name"],
        hashed_password=get_password_hash(user_data["password"])
    )
    session.add(db_user)
    session.commit()
    session.refresh(db_user)

    return {**user_data, "id": db_user.id, "db_user": db_user}

@pytest.fixture
def test_admin(session):
    """Create a test admin user and return their data"""
    import uuid

    unique_id = str(uuid.uuid4())[:8]
    admin_data = {
        "email": f"admin{unique_id}@example.com",
        "username": f"adminuser{unique_id}",
        "password": "AdminPass123!",
        "name": "Admin User"
    }

    db_admin = User(
        email=admin_data["email"],
        username=admin_data["username"],
        name=admin_data["name"],
        hashed_password=get_password_hash(admin_data["password"]),
        is_admin=True
    )
    session.add(db_admin)
    session.commit()
    session.refresh(db_admin)

    return {**admin_data, "id": db_admin.id, "db_user": db_admin}

@pytest.fixture
def auth_headers(test_user):
    """Get authorization headers for test user"""
    from datetime import timedelta

    access_token = create_access_token(
        data={"sub": test_user["username"]},
        expires_delta=timedelta(minutes=30),
        is_admin=test_user["db_user"].is_admin
    )
    return {"Authorization": f"Bearer {access_token}"}

@pytest.fixture
def admin_auth_headers(test_admin):
    """Get authorization headers for admin user"""
    from datetime import timedelta

    access_token = create_access_token(
        data={"sub": test_admin["username"]},
        expires_delta=timedelta(minutes=30),
        is_admin=test_admin["db_user"].is_admin
    )
    return {"Authorization": f"Bearer {access_token}"}