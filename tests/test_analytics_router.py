import pytest
import uuid
from fastapi.testclient import TestClient
from app.main import app

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
    login = client.post("/login", data={
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
    login = client.post("/login", data={
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

def test_time_in_range():
    # Generate unique identifiers for this test run
    unique_id = str(uuid.uuid4())[:8]
    email = f"timeinrangetest{unique_id}@example.com"
    username = f"timeinrangetestuser{unique_id}"
    
    # Register and login user
    client.post("/users", json={
        "email": email,
        "username": username,
        "password": "testpassword",
        "name": "Time in Range Test User"
    })
    login = client.post("/login", data={
        "username": username,
        "password": "testpassword"
    })
    assert login.status_code == 200
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Add glucose readings in different ranges
    readings = [
        {"value": 50, "unit": "mg/dl"},   # Very low
        {"value": 60, "unit": "mg/dl"},   # Low
        {"value": 80, "unit": "mg/dl"},   # In range
        {"value": 120, "unit": "mg/dl"},  # In range
        {"value": 160, "unit": "mg/dl"},  # In range
        {"value": 200, "unit": "mg/dl"},  # High
        {"value": 300, "unit": "mg/dl"},  # Very high
    ]
    
    for reading in readings:
        client.post("/glucose-readings", json=reading, headers=headers)
    
    # Test time-in-range endpoint
    response = client.get("/analytics/time-in-range", headers=headers)
    assert response.status_code == 200
    data = response.json()
    
    # Check structure
    assert "time_in_range" in data
    assert "counts" in data
    assert "meta" in data
    
    # Check time_in_range percentages
    time_in_range = data["time_in_range"]
    assert "very_low" in time_in_range
    assert "low" in time_in_range
    assert "in_range" in time_in_range
    assert "high" in time_in_range
    assert "very_high" in time_in_range
    
    # Check counts
    counts = data["counts"]
    assert "very_low" in counts
    assert "low" in counts
    assert "in_range" in counts
    assert "high" in counts
    assert "very_high" in counts
    
    # Check meta
    meta = data["meta"]
    assert "very_low_threshold" in meta
    assert "low_threshold" in meta
    assert "target_low" in meta
    assert "target_high" in meta
    assert "high_threshold" in meta
    assert "very_high_threshold" in meta
    assert "unit" in meta
    assert "show_percentage" in meta
    assert "total_readings" in meta
    
    # Verify percentages sum to 100 (approximately)
    total_percentage = sum(time_in_range.values())
    assert abs(total_percentage - 100.0) < 0.1
    
    # Verify counts sum to total readings
    total_count = sum(counts.values())
    assert total_count == meta["total_readings"]
    
    # Test with show_percentage=False
    response_absolute = client.get("/analytics/time-in-range?show_percentage=false", headers=headers)
    assert response_absolute.status_code == 200
    data_absolute = response_absolute.json()
    
    # Verify absolute values are returned
    time_in_range_absolute = data_absolute["time_in_range"]
    assert isinstance(time_in_range_absolute["very_low"], int)
    assert isinstance(time_in_range_absolute["low"], int)
    assert isinstance(time_in_range_absolute["in_range"], int)
    assert isinstance(time_in_range_absolute["high"], int)
    assert isinstance(time_in_range_absolute["very_high"], int) 