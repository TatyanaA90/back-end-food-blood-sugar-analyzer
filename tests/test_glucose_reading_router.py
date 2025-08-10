import pytest
import uuid

def test_create_glucose_reading(client, test_user, auth_headers):
    # Create glucose reading
    response = client.post("/glucose-readings", json={
        "value": 120,
        "unit": "mg/dl"
    }, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["value"] == 120
    assert data["unit"] == "mg/dl"