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

def test_glucose_variability():
    # Generate unique identifiers for this test run
    unique_id = str(uuid.uuid4())[:8]
    email = f"glucosevariabilitytest{unique_id}@example.com"
    username = f"glucosevariabilitytestuser{unique_id}"
    
    # Register and login user
    client.post("/users", json={
        "email": email,
        "username": username,
        "password": "testpassword",
        "name": "Glucose Variability Test User"
    })
    login = client.post("/login", data={
        "username": username,
        "password": "testpassword"
    })
    assert login.status_code == 200
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Add glucose readings with known variability
    # These values will give us predictable SD, CV, and GMI
    readings = [
        {"value": 100, "unit": "mg/dl"},  # Low variability set
        {"value": 110, "unit": "mg/dl"},
        {"value": 105, "unit": "mg/dl"},
        {"value": 115, "unit": "mg/dl"},
        {"value": 108, "unit": "mg/dl"},
        {"value": 112, "unit": "mg/dl"},
    ]
    
    for reading in readings:
        client.post("/glucose-readings", json=reading, headers=headers)
    
    # Test glucose-variability endpoint
    response = client.get("/analytics/glucose-variability", headers=headers)
    assert response.status_code == 200
    data = response.json()
    
    # Check structure
    assert "variability_metrics" in data
    assert "meta" in data
    assert "explanations" in data
    
    # Check variability_metrics
    metrics = data["variability_metrics"]
    assert "standard_deviation" in metrics
    assert "coefficient_of_variation" in metrics
    assert "glucose_management_indicator" in metrics
    assert "mean_glucose" in metrics
    assert "min_glucose" in metrics
    assert "max_glucose" in metrics
    assert "total_readings" in metrics
    
    # Verify data types
    assert isinstance(metrics["standard_deviation"], (int, float))
    assert isinstance(metrics["coefficient_of_variation"], (int, float))
    assert isinstance(metrics["glucose_management_indicator"], (int, float))
    assert isinstance(metrics["mean_glucose"], (int, float))
    assert isinstance(metrics["min_glucose"], (int, float))
    assert isinstance(metrics["max_glucose"], (int, float))
    assert isinstance(metrics["total_readings"], int)
    
    # Verify calculations are reasonable
    assert metrics["total_readings"] == 6
    assert metrics["min_glucose"] == 100
    assert metrics["max_glucose"] == 115
    assert 100 <= metrics["mean_glucose"] <= 115
    assert metrics["standard_deviation"] > 0
    assert metrics["coefficient_of_variation"] > 0
    assert 5.0 <= metrics["glucose_management_indicator"] <= 8.0  # Reasonable GMI range
    
    # Check explanations
    explanations = data["explanations"]
    assert "standard_deviation" in explanations
    assert "coefficient_of_variation" in explanations
    assert "glucose_management_indicator" in explanations
    assert "overall_assessment" in explanations
    
    # Verify explanations are strings
    assert isinstance(explanations["standard_deviation"], str)
    assert isinstance(explanations["coefficient_of_variation"], str)
    assert isinstance(explanations["glucose_management_indicator"], str)
    assert isinstance(explanations["overall_assessment"], str)
    
    # Check meta
    meta = data["meta"]
    assert "total_readings" in meta
    assert "include_explanations" in meta
    assert meta["total_readings"] == 6
    assert meta["include_explanations"] == True

def test_glucose_variability_no_explanations():
    # Generate unique identifiers for this test run
    unique_id = str(uuid.uuid4())[:8]
    email = f"glucosevariabilitynoexp{unique_id}@example.com"
    username = f"glucosevariabilitynoexpuser{unique_id}"
    
    # Register and login user
    client.post("/users", json={
        "email": email,
        "username": username,
        "password": "testpassword",
        "name": "Glucose Variability No Explanations Test User"
    })
    login = client.post("/login", data={
        "username": username,
        "password": "testpassword"
    })
    assert login.status_code == 200
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Add glucose readings
    readings = [
        {"value": 120, "unit": "mg/dl"},
        {"value": 140, "unit": "mg/dl"},
        {"value": 130, "unit": "mg/dl"},
    ]
    
    for reading in readings:
        client.post("/glucose-readings", json=reading, headers=headers)
    
    # Test without explanations
    response = client.get("/analytics/glucose-variability?include_explanations=false", headers=headers)
    assert response.status_code == 200
    data = response.json()
    
    # Check structure
    assert "variability_metrics" in data
    assert "meta" in data
    assert "explanations" not in data  # Should not include explanations
    
    # Check meta
    meta = data["meta"]
    assert meta["include_explanations"] == False

def test_glucose_variability_insufficient_data():
    # Generate unique identifiers for this test run
    unique_id = str(uuid.uuid4())[:8]
    email = f"glucosevariabilityinsufficient{unique_id}@example.com"
    username = f"glucosevariabilityinsufficientuser{unique_id}"
    
    # Register and login user
    client.post("/users", json={
        "email": email,
        "username": username,
        "password": "testpassword",
        "name": "Glucose Variability Insufficient Data Test User"
    })
    login = client.post("/login", data={
        "username": username,
        "password": "testpassword"
    })
    assert login.status_code == 200
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Add only one glucose reading (insufficient for variability calculation)
    client.post("/glucose-readings", json={"value": 120, "unit": "mg/dl"}, headers=headers)
    
    # Test with insufficient data
    response = client.get("/analytics/glucose-variability", headers=headers)
    assert response.status_code == 200
    data = response.json()
    
    # Check structure
    assert "variability_metrics" in data
    assert "explanations" in data
    assert "meta" in data
    
    # Check that metrics are None
    metrics = data["variability_metrics"]
    assert metrics["standard_deviation"] is None
    assert metrics["coefficient_of_variation"] is None
    assert metrics["glucose_management_indicator"] is None
    
    # Check explanations explain the issue
    explanations = data["explanations"]
    assert "Not enough data to calculate variability" in explanations["standard_deviation"]
    assert "Not enough data to calculate variability" in explanations["coefficient_of_variation"]
    assert "Not enough data to calculate GMI" in explanations["glucose_management_indicator"]
    
    # Check meta
    meta = data["meta"]
    assert meta["total_readings"] == 1

def test_glucose_variability_high_variability():
    # Generate unique identifiers for this test run
    unique_id = str(uuid.uuid4())[:8]
    email = f"glucosevariabilityhigh{unique_id}@example.com"
    username = f"glucosevariabilityhighuser{unique_id}"
    
    # Register and login user
    client.post("/users", json={
        "email": email,
        "username": username,
        "password": "testpassword",
        "name": "Glucose Variability High Test User"
    })
    login = client.post("/login", data={
        "username": username,
        "password": "testpassword"
    })
    assert login.status_code == 200
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Add glucose readings with high variability
    readings = [
        {"value": 60, "unit": "mg/dl"},   # Very low
        {"value": 80, "unit": "mg/dl"},   # Low
        {"value": 120, "unit": "mg/dl"},  # Normal
        {"value": 200, "unit": "mg/dl"},  # High
        {"value": 300, "unit": "mg/dl"},  # Very high
    ]
    
    for reading in readings:
        client.post("/glucose-readings", json=reading, headers=headers)
    
    # Test high variability scenario
    response = client.get("/analytics/glucose-variability", headers=headers)
    assert response.status_code == 200
    data = response.json()
    
    # Check metrics
    metrics = data["variability_metrics"]
    assert metrics["total_readings"] == 5
    assert metrics["min_glucose"] == 60
    assert metrics["max_glucose"] == 300
    
    # High variability should result in high SD and CV
    assert metrics["standard_deviation"] > 50  # Should be high
    assert metrics["coefficient_of_variation"] > 30  # Should be high
    
    # Check explanations reflect high variability
    explanations = data["explanations"]
    assert "High variability" in explanations["standard_deviation"] or "needs attention" in explanations["standard_deviation"]
    assert "High variability" in explanations["coefficient_of_variation"] or "significantly" in explanations["coefficient_of_variation"] 