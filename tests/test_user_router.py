import pytest
import uuid
from datetime import datetime, timedelta, UTC
from fastapi.testclient import TestClient
from sqlmodel import Session, select
from app.main import app
from app.models.user import User
from app.core.security import get_password_hash, create_access_token

client = TestClient(app)

@pytest.fixture
def test_db_session():
    from app.core.database import get_session
    return next(get_session())

@pytest.fixture
def test_user(test_db_session: Session):
    """Create a test user and return their data"""
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
    test_db_session.add(db_user)
    test_db_session.commit()
    test_db_session.refresh(db_user)
    
    return {**user_data, "id": db_user.id, "db_user": db_user}

@pytest.fixture
def test_admin(test_db_session: Session):
    """Create a test admin user and return their data"""
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
    test_db_session.add(db_admin)
    test_db_session.commit()
    test_db_session.refresh(db_admin)
    
    return {**admin_data, "id": db_admin.id, "db_user": db_admin}

@pytest.fixture
def auth_headers(test_user):
    """Get authorization headers for test user"""
    access_token = create_access_token(
        data={"sub": test_user["username"]},
        expires_delta=timedelta(minutes=30),
        is_admin=test_user["db_user"].is_admin
    )
    return {"Authorization": f"Bearer {access_token}"}

@pytest.fixture
def admin_auth_headers(test_admin):
    """Get authorization headers for admin user"""
    access_token = create_access_token(
        data={"sub": test_admin["username"]},
        expires_delta=timedelta(minutes=30),
        is_admin=test_admin["db_user"].is_admin
    )
    return {"Authorization": f"Bearer {access_token}"}

def test_user_registration():
    """Test user registration endpoint"""
    unique_id = str(uuid.uuid4())[:8]
    response = client.post("/users", json={
        "email": f"apitest{unique_id}@example.com",
        "username": f"apitestuser{unique_id}",
        "password": "TestPass123!",
        "name": "Test User"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "token_type" in data
    assert "user" in data
    assert data["user"]["email"] == f"apitest{unique_id}@example.com"
    assert data["user"]["username"] == f"apitestuser{unique_id}"
    assert data["user"]["name"] == "Test User"

def test_user_registration_duplicate_email(test_user):
    """Test registration with duplicate email"""
    response = client.post("/users", json={
        "email": test_user["email"],
        "username": "newusername",
        "password": "TestPass123!",
        "name": "New User"
    })
    assert response.status_code == 409
    assert "exists" in response.json()["detail"].lower()

def test_user_login():
    """Test user login endpoint"""
    unique_id = str(uuid.uuid4())[:8]
    user_data = {
        "email": f"logintest{unique_id}@example.com",
        "username": f"loginuser{unique_id}",
        "password": "TestPass123!",
        "name": "Login Test User"
    }
    
    # Register first
    client.post("/users", json=user_data)
    
    # Try login
    response = client.post("/login", json={
        "username": user_data["username"],
        "password": user_data["password"]
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["username"] == user_data["username"]

def test_get_current_user(test_user, auth_headers):
    """Test getting current user profile"""
    response = client.get("/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user["email"]
    assert data["username"] == test_user["username"]

def test_update_profile(test_user, auth_headers):
    """Test updating user profile"""
    new_data = {
        "name": "Updated Name",
        "email": f"updated{test_user['email']}",
        "weight": 75.5,
        "weight_unit": "kg"
    }
    response = client.put("/me", json=new_data, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == new_data["name"]
    assert data["email"] == new_data["email"]

def test_change_password(test_user, auth_headers, test_db_session):
    """Test changing user password"""
    response = client.post("/me/change-password", json={
        "current_password": test_user["password"],
        "new_password": "NewTestPass123!"
    }, headers=auth_headers)
    assert response.status_code == 200
    
    # Try login with new password
    response = client.post("/login", json={
        "username": test_user["username"],
        "password": "NewTestPass123!"
    })
    assert response.status_code == 200

def test_forgot_password(test_user):
    """Test password reset request"""
    response = client.post("/forgot-password", json={
        "email": test_user["email"]
    })
    assert response.status_code == 200
    assert "message" in response.json()

def test_reset_password(test_user, test_db_session):
    """Test password reset with token"""
    # Set up reset token
    reset_token = str(uuid.uuid4())
    test_user["db_user"].reset_token = reset_token
    test_user["db_user"].reset_token_expires = datetime.now(UTC) + timedelta(hours=1)
    test_db_session.add(test_user["db_user"])
    test_db_session.commit()
    
    response = client.post("/reset-password", json={
        "token": reset_token,
        "new_password": "ResetPass123!"
    })
    assert response.status_code == 200
    
    # Try login with new password
    response = client.post("/login", json={
        "username": test_user["username"],
        "password": "ResetPass123!"
    })
    assert response.status_code == 200

def test_admin_reset_user_password(test_user, test_admin, admin_auth_headers):
    """Test admin resetting user password"""
    response = client.post("/admin/reset-password", json={
        "user_id": test_user["id"],
        "new_password": "AdminReset123!"
    }, headers=admin_auth_headers)
    assert response.status_code == 200
    
    # Try login with new password
    response = client.post("/login", json={
        "username": test_user["username"],
        "password": "AdminReset123!"
    })
    assert response.status_code == 200

def test_delete_user(test_user, auth_headers):
    """Test user account deletion"""
    response = client.delete(f"/users/{test_user['id']}", headers=auth_headers)
    assert response.status_code == 200
    
    # Try to get deleted user
    response = client.get(f"/users/{test_user['id']}", headers=auth_headers)
    assert response.status_code in [401, 404]

def test_admin_delete_user(test_user, test_admin, admin_auth_headers):
    """Test admin deleting user account"""
    response = client.delete(f"/users/{test_user['id']}", headers=admin_auth_headers)
    assert response.status_code == 200
    assert "deleted" in response.json()["message"].lower()

def test_admin_get_user_stats(test_admin, admin_auth_headers):
    """Test getting user statistics"""
    response = client.get("/users/stats/count", headers=admin_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "total_users" in data
    assert isinstance(data["total_users"], int)

def test_non_admin_operations_fail(test_user, auth_headers):
    """Test that non-admin users cannot access admin endpoints"""
    # Try to get user stats
    response = client.get("/users/stats/count", headers=auth_headers)
    assert response.status_code == 403
    
    # Try to delete another user
    response = client.delete(f"/users/{test_user['id'] + 1}", headers=auth_headers)
    assert response.status_code == 403
    
    # Try to reset another user's password
    response = client.post("/admin/reset-password", json={
        "user_id": test_user["id"] + 1,
        "new_password": "Unauthorized123!"
    }, headers=auth_headers)
    assert response.status_code == 403