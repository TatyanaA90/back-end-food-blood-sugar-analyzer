import pytest
import uuid
from datetime import datetime, timedelta, UTC
from fastapi.testclient import TestClient
from app.main import app
from sqlalchemy import select

client = TestClient(app)

def test_glucose_summary_whole_range():
    # Generate unique identifiers for this test run
    unique_id = str(uuid.uuid4())[:8]
    email = f"analyticsapitest{unique_id}@example.com"
    username = f"analyticsapitestuser{unique_id}"
    
    # Register and login user
    client.post("/users", json={
        "email": email,
        "username": username,
        "password": "testpassword",
        "name": "Analytics Test User"
    })
    login = client.post("/login", json={
        "username": username,
        "password": "testpassword"
    })
    assert login.status_code == 200  # Ensure login succeeded
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    # Add a glucose reading
    client.post("/glucose-readings", json={
        "value": 110,
        "unit": "mg/dl"
    }, headers=headers)
    # Test whole-range summary
    response = client.get("/analytics/glucose-summary", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "average" in data
    assert "min" in data
    assert "max" in data
    assert "std_dev" in data
    assert "num_readings" in data
    assert "in_target_percent" in data

def test_glucose_summary_by_day():
    # Generate unique identifiers for this test run
    unique_id = str(uuid.uuid4())[:8]
    email = f"analyticsapitest2{unique_id}@example.com"
    username = f"analyticsapitestuser2{unique_id}"
    
    # Register and login user
    client.post("/users", json={
        "email": email,
        "username": username,
        "password": "testpassword",
        "name": "Analytics Test User 2"
    })
    login = client.post("/login", json={
        "username": username,
        "password": "testpassword"
    })
    assert login.status_code == 200  # Ensure login succeeded
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    # Add a glucose reading
    client.post("/glucose-readings", json={
        "value": 120,
        "unit": "mg/dl"
    }, headers=headers)
    # Test group_by=day
    response = client.get("/analytics/glucose-summary?group_by=day", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "meta" in data