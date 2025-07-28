import pytest
import uuid
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_meal():
    # Generate unique identifiers for this test run
    unique_id = str(uuid.uuid4())[:8]
    email = f"mealapitest{unique_id}@example.com"
    username = f"mealapitestuser{unique_id}"
    
    # Register and login user
    client.post("/users", json={
        "email": email,
        "username": username,
        "password": "testpassword",
        "name": "Meal Test User"
    })
    login = client.post("/login", data={
        "username": username,
        "password": "testpassword"
    })
    assert login.status_code == 200  # Ensure login succeeded
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    # Create meal
    response = client.post("/meals", json={
        "description": "Test Meal",
        "ingredients": [
            {"name": "Rice", "weight": 100, "carbs": 28}
        ]
    }, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["description"] == "Test Meal"
    assert data["total_carbs"] == 28 