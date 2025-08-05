import pytest
import uuid
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_glucose_reading():
    # Generate unique identifiers for this test run
    unique_id = str(uuid.uuid4())[:8]
    email = f"glucoseapitest{unique_id}@example.com"
    username = f"glucoseapitestuser{unique_id}"
    
    # Register and login user
    client.post("/users", json={
        "email": email,
        "username": username,
        "password": "testpassword",
        "name": "Glucose Test User"
    })
    login = client.post("/login", json={
        "username": username,
        "password": "testpassword"
    })
    assert login.status_code == 200  # Ensure login succeeded
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    # Create glucose reading
    response = client.post("/glucose-readings", json={
        "value": 120,
        "unit": "mg/dl"
    }, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["value"] == 120
    assert data["unit"] == "mg/dl"