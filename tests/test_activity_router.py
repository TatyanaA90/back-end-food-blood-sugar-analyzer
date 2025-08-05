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
    login = client.post("/login", json={
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

def test_create_activity_with_start_end_time():
    """Test creating activity with start and end times."""
    # Generate unique identifiers for this test run
    unique_id = str(uuid.uuid4())[:8]
    email = f"activitytime{unique_id}@example.com"
    username = f"activitytimeuser{unique_id}"
    
    # Register and login user
    client.post("/users", json={
        "email": email,
        "username": username,
        "password": "testpassword",
        "name": "Activity Time Test User"
    })
    login = client.post("/login", json={
        "username": username,
        "password": "testpassword"
    })
    assert login.status_code == 200
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create activity with start and end times
    from datetime import datetime, timedelta, UTC
    start_time = datetime.now(UTC)
    end_time = start_time + timedelta(minutes=45)
    
    response = client.post("/activities", json={
        "type": "Walking",
        "intensity": "Low",
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat()
    }, headers=headers)
    
    assert response.status_code == 201
    data = response.json()
    assert data["type"] == "Walking"
    assert data["duration_min"] == 45  # Auto-calculated
    assert "calories_burned" in data

def test_get_previous_activities():
    """Test getting previous activities for auto-save suggestions."""
    # Generate unique identifiers for this test run
    unique_id = str(uuid.uuid4())[:8]
    email = f"previous{unique_id}@example.com"
    username = f"previoususer{unique_id}"
    
    # Register and login user
    client.post("/users", json={
        "email": email,
        "username": username,
        "password": "testpassword",
        "name": "Previous Activities Test User"
    })
    login = client.post("/login", json={
        "username": username,
        "password": "testpassword"
    })
    assert login.status_code == 200
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create a few activities
    activities = [
        {"type": "Running", "intensity": "High", "duration_min": 30},
        {"type": "Walking", "intensity": "Low", "duration_min": 60},
        {"type": "Cycling", "intensity": "Medium", "duration_min": 45}
    ]
    
    for activity in activities:
        response = client.post("/activities", json=activity, headers=headers)
        assert response.status_code == 201
    
    # Get previous activities
    response = client.get("/activities/previous-activities?limit=5", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) <= 5
    assert all("type" in activity for activity in data)