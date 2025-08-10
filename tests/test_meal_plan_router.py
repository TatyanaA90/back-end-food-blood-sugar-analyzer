import pytest
import uuid

def test_create_meal(client, test_user, auth_headers):
    # Create meal
    response = client.post("/meals", json={
        "description": "Test Meal",
        "ingredients": [
            {"name": "Rice", "weight": 100, "carbs": 28}
        ]
    }, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["description"] == "Test Meal"
    assert data["total_carbs"] == 28