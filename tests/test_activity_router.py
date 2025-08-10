import pytest
from datetime import datetime, timedelta, UTC

def test_create_activity(client, test_user, auth_headers):
    """Test creating an activity"""
    response = client.post("/activities", json={
        "type": "Running",
        "intensity": "High",
        "duration_min": 30
    }, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["type"] == "Running"
    assert "calories_burned" in data

def test_create_activity_with_start_end_time(client, test_user, auth_headers):
    """Test creating activity with start and end times."""
    start_time = datetime.now(UTC)
    end_time = start_time + timedelta(minutes=45)

    response = client.post("/activities", json={
        "type": "Walking",
        "intensity": "Low",
        "start_time": start_time.isoformat(),
        "end_time": end_time.isoformat()
    }, headers=auth_headers)

    assert response.status_code == 201
    data = response.json()
    assert data["type"] == "Walking"
    assert data["duration_min"] == 45  # Auto-calculated
    assert "calories_burned" in data

def test_get_previous_activities(client, test_user, auth_headers):
    """Test getting previous activities for auto-save suggestions."""
    # First create some activities
    activities = [
        {"type": "Running", "intensity": "High", "duration_min": 30},
        {"type": "Walking", "intensity": "Low", "duration_min": 20},
        {"type": "Cycling", "intensity": "Medium", "duration_min": 45}
    ]

    for activity in activities:
        response = client.post("/activities", json=activity, headers=auth_headers)
        assert response.status_code == 201

    # Get previous activities
    response = client.get("/activities/previous-activities", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 3  # Should have at least the activities we created