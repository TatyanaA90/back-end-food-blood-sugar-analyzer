import pytest
import uuid
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_activity():
    # Generate unique identifiers for this test run
    unique_id = str(uuid.uuid4())[:8]
    email = f"activityapitest{unique_id}@example.com"
    username = f"activityapitestuser{unique_id}"
    
    # Register and login user
    client.post("/users", json={
        "email": email,
        "username": username,
        "password": "testpassword",
        "name": "Activity Test User"
    })
    login = client.post("/login", data={
        "username": username,
        "password": "testpassword"
    })
    assert login.status_code == 200  # Ensure login succeeded
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    # Create activity
    response = client.post("/activities", json={
        "type": "Running",
        "intensity": "High",
        "duration_min": 30
    }, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["type"] == "Running"
    assert "calories_burned" in data 