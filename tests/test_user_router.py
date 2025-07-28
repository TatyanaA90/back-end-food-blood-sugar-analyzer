import pytest
import uuid
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_user_registration():
    # Generate unique identifiers for this test run
    unique_id = str(uuid.uuid4())[:8]
    email = f"apitest{unique_id}@example.com"
    username = f"apitestuser{unique_id}"
    
    response = client.post("/users", json={
        "email": email,
        "username": username,
        "password": "testpassword",
        "name": "Test User"
    })
    assert response.status_code == 200 or response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["username"] == username
    assert data["name"] == "Test User"

def test_user_login():
    # Generate unique identifiers for this test run
    unique_id = str(uuid.uuid4())[:8]
    email = f"apitest2{unique_id}@example.com"
    username = f"apitestuser2{unique_id}"
    
    # Register first (if not already)
    client.post("/users", json={
        "email": email,
        "username": username,
        "password": "testpassword",
        "name": "Test User 2"
    })
    response = client.post("/login", data={
        "username": username,
        "password": "testpassword"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer" 