import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy.pool import StaticPool
from app.core.database import get_session
from app.core.config import settings
from app.main import app

@pytest.fixture(scope="session")
def test_engine():
    """Create a test database engine"""
    # Use in-memory SQLite for tests
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
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