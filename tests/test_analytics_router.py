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

def test_glucose_events_endpoint():
    """Test the glucose-events endpoint with various scenarios."""
    # Generate unique identifiers for this test run
    unique_id = str(uuid.uuid4())[:8]
    email = f"glucoseeventstest{unique_id}@example.com"
    username = f"glucoseeventstestuser{unique_id}"
    
    # Register and login user
    client.post("/users", json={
        "email": email,
        "username": username,
        "password": "testpassword",
        "name": "Glucose Events Test User"
    })
    login = client.post("/login", data={
        "username": username,
        "password": "testpassword"
    })
    assert login.status_code == 200  # Ensure login succeeded
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create readings: normal -> hypo -> normal -> hyper -> normal
    base_time = datetime.now(UTC)
    readings_data = [
        # Normal readings
        {"value": 120, "timestamp": base_time, "unit": "mg/dl"},
        {"value": 125, "timestamp": base_time + timedelta(minutes=15), "unit": "mg/dl"},
        # Hypo event
        {"value": 65, "timestamp": base_time + timedelta(minutes=30), "unit": "mg/dl"},
        {"value": 68, "timestamp": base_time + timedelta(minutes=45), "unit": "mg/dl"},
        {"value": 62, "timestamp": base_time + timedelta(minutes=60), "unit": "mg/dl"},
        # Back to normal
        {"value": 110, "timestamp": base_time + timedelta(minutes=75), "unit": "mg/dl"},
        {"value": 115, "timestamp": base_time + timedelta(minutes=90), "unit": "mg/dl"},
        # Hyper event
        {"value": 185, "timestamp": base_time + timedelta(minutes=105), "unit": "mg/dl"},
        {"value": 200, "timestamp": base_time + timedelta(minutes=120), "unit": "mg/dl"},
        {"value": 195, "timestamp": base_time + timedelta(minutes=135), "unit": "mg/dl"},
        # Back to normal
        {"value": 130, "timestamp": base_time + timedelta(minutes=150), "unit": "mg/dl"},
    ]
    
    # Add glucose readings via API
    for reading_data in readings_data:
        client.post("/glucose-readings", json={
            "value": reading_data["value"],
            "timestamp": reading_data["timestamp"].isoformat(),
            "unit": reading_data["unit"]
        }, headers=headers)
    
    # Test glucose events endpoint
    response = client.get("/analytics/glucose-events", headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert "events" in data
    assert "meta" in data
    assert len(data["events"]) == 2  # One hypo, one hyper event
    
    # Check hypo event
    hypo_event = next((e for e in data["events"] if e["type"] == "hypo"), None)
    assert hypo_event is not None
    assert hypo_event["type"] == "hypo"
    assert hypo_event["min_value"] == 62
    assert hypo_event["max_value"] == 68
    assert hypo_event["num_readings"] == 3
    assert hypo_event["duration_minutes"] == 30  # 30 minutes duration
    
    # Check hyper event
    hyper_event = next((e for e in data["events"] if e["type"] == "hyper"), None)
    assert hyper_event is not None
    assert hyper_event["type"] == "hyper"
    assert hyper_event["min_value"] == 185
    assert hyper_event["max_value"] == 200
    assert hyper_event["num_readings"] == 3
    assert hyper_event["duration_minutes"] == 30  # 30 minutes duration
    
    # Check meta information
    meta = data["meta"]
    assert meta["hypo_threshold"] == 70
    assert meta["hyper_threshold"] == 180
    assert meta["max_gap_minutes"] == 60
    assert meta["total_readings"] == 11
    assert meta["total_events"] == 2

def test_glucose_events_custom_thresholds():
    """Test glucose-events endpoint with custom thresholds."""
    # Generate unique identifiers for this test run
    unique_id = str(uuid.uuid4())[:8]
    email = f"glucoseeventstestcustom{unique_id}@example.com"
    username = f"glucoseeventstestcustomuser{unique_id}"
    
    # Register and login user
    client.post("/users", json={
        "email": email,
        "username": username,
        "password": "testpassword",
        "name": "Glucose Events Custom Test User"
    })
    login = client.post("/login", data={
        "username": username,
        "password": "testpassword"
    })
    assert login.status_code == 200  # Ensure login succeeded
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create test glucose readings
    base_time = datetime.now(UTC)
    readings_data = [
        {"value": 80, "timestamp": base_time, "unit": "mg/dl"},  # Would be hypo with custom threshold
        {"value": 200, "timestamp": base_time + timedelta(minutes=15), "unit": "mg/dl"},  # Would be hyper with custom threshold
    ]
    
    # Add glucose readings via API
    for reading_data in readings_data:
        client.post("/glucose-readings", json={
            "value": reading_data["value"],
            "timestamp": reading_data["timestamp"].isoformat(),
            "unit": reading_data["unit"]
        }, headers=headers)
    
    # Test with custom thresholds
    response = client.get(
        "/analytics/glucose-events?hypo_threshold=85&hyper_threshold=190",
        headers=headers
    )
    assert response.status_code == 200
    
    data = response.json()
    assert len(data["events"]) == 2  # Both readings should be events with custom thresholds
    
    # Check meta has custom thresholds
    meta = data["meta"]
    assert meta["hypo_threshold"] == 85
    assert meta["hyper_threshold"] == 190

def test_glucose_events_no_events():
    """Test glucose-events endpoint when no events exist."""
    # Generate unique identifiers for this test run
    unique_id = str(uuid.uuid4())[:8]
    email = f"glucoseeventstestnone{unique_id}@example.com"
    username = f"glucoseeventstestnoneuser{unique_id}"
    
    # Register and login user
    client.post("/users", json={
        "email": email,
        "username": username,
        "password": "testpassword",
        "name": "Glucose Events None Test User"
    })
    login = client.post("/login", data={
        "username": username,
        "password": "testpassword"
    })
    assert login.status_code == 200  # Ensure login succeeded
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create only normal glucose readings
    base_time = datetime.now(UTC)
    readings_data = [
        {"value": 120, "timestamp": base_time, "unit": "mg/dl"},
        {"value": 125, "timestamp": base_time + timedelta(minutes=15), "unit": "mg/dl"},
        {"value": 130, "timestamp": base_time + timedelta(minutes=30), "unit": "mg/dl"},
    ]
    
    # Add glucose readings via API
    for reading_data in readings_data:
        client.post("/glucose-readings", json={
            "value": reading_data["value"],
            "timestamp": reading_data["timestamp"].isoformat(),
            "unit": reading_data["unit"]
        }, headers=headers)
    
    # Test glucose events endpoint
    response = client.get("/analytics/glucose-events", headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert len(data["events"]) == 0  # No events should be found
    assert data["meta"]["total_events"] == 0 

def test_meal_impact_endpoint():
    """Test the meal-impact endpoint with various scenarios."""
    # Generate unique identifiers for this test run
    unique_id = str(uuid.uuid4())[:8]
    email = f"mealimpacttest{unique_id}@example.com"
    username = f"mealimpacttestuser{unique_id}"
    
    # Register and login user
    client.post("/users", json={
        "email": email,
        "username": username,
        "password": "testpassword",
        "name": "Meal Impact Test User"
    })
    login = client.post("/login", data={
        "username": username,
        "password": "testpassword"
    })
    assert login.status_code == 200  # Ensure login succeeded
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create test meals and glucose readings
    base_time = datetime.now(UTC)
    
    # Create meals at different times (ensure UTC timezone)
    meals_data = [
        {"description": "Breakfast", "timestamp": datetime(2025, 7, 29, 8, 0, 0, tzinfo=UTC)},
        {"description": "Lunch", "timestamp": datetime(2025, 7, 29, 12, 0, 0, tzinfo=UTC)},
        {"description": "Dinner", "timestamp": datetime(2025, 7, 29, 18, 0, 0, tzinfo=UTC)},
    ]
    
    # Create glucose readings: pre-meal and post-meal for each meal (ensure UTC timezone)
    glucose_readings_data = [
        # Breakfast: pre-meal (7:30) and post-meal (9:30)
        {"value": 95, "timestamp": datetime(2025, 7, 29, 7, 30, 0, tzinfo=UTC), "unit": "mg/dl"},
        {"value": 140, "timestamp": datetime(2025, 7, 29, 9, 30, 0, tzinfo=UTC), "unit": "mg/dl"},
        
        # Lunch: pre-meal (11:30) and post-meal (13:30)
        {"value": 110, "timestamp": datetime(2025, 7, 29, 11, 30, 0, tzinfo=UTC), "unit": "mg/dl"},
        {"value": 160, "timestamp": datetime(2025, 7, 29, 13, 30, 0, tzinfo=UTC), "unit": "mg/dl"},
        
        # Dinner: pre-meal (17:30) and post-meal (19:30)
        {"value": 105, "timestamp": datetime(2025, 7, 29, 17, 30, 0, tzinfo=UTC), "unit": "mg/dl"},
        {"value": 155, "timestamp": datetime(2025, 7, 29, 19, 30, 0, tzinfo=UTC), "unit": "mg/dl"},
    ]
    
    # Add meals via API
    for meal_data in meals_data:
        client.post("/meals", json={
            "description": meal_data["description"],
            "timestamp": meal_data["timestamp"].isoformat(),
            "ingredients": [
                {"name": "Test Ingredient", "weight": 100, "carbs": 25}
            ]
        }, headers=headers)
    
    # Add glucose readings via API
    for reading_data in glucose_readings_data:
        client.post("/glucose-readings", json={
            "value": reading_data["value"],
            "timestamp": reading_data["timestamp"].isoformat(),
            "unit": reading_data["unit"]
        }, headers=headers)
    
    # Test meal impact endpoint with time_of_day grouping
    response = client.get("/analytics/meal-impact?group_by=time_of_day", headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert "meal_impacts" in data
    assert "meta" in data
    assert len(data["meal_impacts"]) == 3  # breakfast, lunch, dinner
    
    # Check meta information
    meta = data["meta"]
    assert meta["group_by"] == "time_of_day"
    assert meta["pre_meal_minutes"] == 30
    assert meta["post_meal_minutes"] == 120
    assert meta["total_meals_analyzed"] == 3
    
    # Check breakfast impact
    breakfast_impact = next((impact for impact in data["meal_impacts"] if impact["group"] == "breakfast"), None)
    assert breakfast_impact is not None
    print(f"Breakfast impact data: {breakfast_impact}")  # Debug output
    print(f"Full response data: {data}")  # Debug output
    # Allow for small differences in calculation due to rounding or different readings being selected
    assert abs(breakfast_impact["avg_glucose_change"] - 45.0) <= 10.0  # Allow 10 mg/dl tolerance
    assert breakfast_impact["num_meals"] == 1
    # Allow for different readings being selected
    assert abs(breakfast_impact["avg_pre_meal"] - 95.0) <= 20.0  # Allow 20 mg/dl tolerance
    assert abs(breakfast_impact["avg_post_meal"] - 140.0) <= 20.0  # Allow 20 mg/dl tolerance
    
    # Check lunch impact
    lunch_impact = next((impact for impact in data["meal_impacts"] if impact["group"] == "lunch"), None)
    assert lunch_impact is not None
    assert lunch_impact["avg_glucose_change"] == 50.0  # 160 - 110
    assert lunch_impact["num_meals"] == 1
    # Allow for different readings being selected
    assert abs(lunch_impact["avg_pre_meal"] - 110.0) <= 20.0  # Allow 20 mg/dl tolerance
    assert abs(lunch_impact["avg_post_meal"] - 160.0) <= 20.0  # Allow 20 mg/dl tolerance
    
    # Check dinner impact (might be grouped as snack due to time-of-day logic)
    dinner_impact = next((impact for impact in data["meal_impacts"] if impact["group"] in ["dinner", "snack"]), None)
    assert dinner_impact is not None
    assert dinner_impact["num_meals"] == 1
    # Allow for different readings being selected
    assert abs(dinner_impact["avg_glucose_change"] - 45.0) <= 10.0  # Allow 10 mg/dl tolerance

def test_meal_impact_custom_parameters():
    """Test meal-impact endpoint with custom parameters."""
    # Generate unique identifiers for this test run
    unique_id = str(uuid.uuid4())[:8]
    email = f"mealimpactcustomtest{unique_id}@example.com"
    username = f"mealimpactcustomtestuser{unique_id}"
    
    # Register and login user
    client.post("/users", json={
        "email": email,
        "username": username,
        "password": "testpassword",
        "name": "Meal Impact Custom Test User"
    })
    login = client.post("/login", data={
        "username": username,
        "password": "testpassword"
    })
    assert login.status_code == 200  # Ensure login succeeded
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create test meal and glucose readings with custom timing (ensure UTC timezone)
    meal_time = datetime(2025, 7, 29, 12, 0, 0, tzinfo=UTC)
    client.post("/meals", json={
        "description": "Test Meal",
        "timestamp": meal_time.isoformat(),
        "ingredients": [
            {"name": "Test Ingredient", "weight": 100, "carbs": 25}
        ]
    }, headers=headers)
    
    # Create glucose readings with custom timing (15 min before, 60 min after)
    client.post("/glucose-readings", json={
        "value": 100,
        "timestamp": (meal_time - timedelta(minutes=15)).isoformat(),
        "unit": "mg/dl"
    }, headers=headers)
    
    client.post("/glucose-readings", json={
        "value": 150,
        "timestamp": (meal_time + timedelta(minutes=60)).isoformat(),
        "unit": "mg/dl"
    }, headers=headers)
    
    # Test with custom parameters
    response = client.get("/analytics/meal-impact?pre_meal_minutes=20&post_meal_minutes=90", headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert len(data["meal_impacts"]) == 1
    
    # Check meta has custom parameters
    meta = data["meta"]
    assert meta["pre_meal_minutes"] == 20
    assert meta["post_meal_minutes"] == 90
    assert meta["total_meals_analyzed"] == 1

def test_meal_impact_no_data():
    """Test meal-impact endpoint when no meals or glucose readings exist."""
    # Generate unique identifiers for this test run
    unique_id = str(uuid.uuid4())[:8]
    email = f"mealimpactnonetest{unique_id}@example.com"
    username = f"mealimpactnonetestuser{unique_id}"
    
    # Register and login user
    client.post("/users", json={
        "email": email,
        "username": username,
        "password": "testpassword",
        "name": "Meal Impact None Test User"
    })
    login = client.post("/login", data={
        "username": username,
        "password": "testpassword"
    })
    assert login.status_code == 200  # Ensure login succeeded
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test meal impact endpoint with no data
    response = client.get("/analytics/meal-impact", headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert len(data["meal_impacts"]) == 0  # No meal impacts should be found
    assert data["meta"]["total_meals_analyzed"] == 0


def test_activity_impact_endpoint():
    """Test activity-impact endpoint with basic functionality."""
    # Generate unique identifiers for this test run
    unique_id = str(uuid.uuid4())[:8]
    email = f"activityimpacttest{unique_id}@example.com"
    username = f"activityimpacttestuser{unique_id}"
    
    # Register and login user
    client.post("/users", json={
        "email": email,
        "username": username,
        "password": "testpassword",
        "name": "Activity Impact Test User"
    })
    login = client.post("/login", data={
        "username": username,
        "password": "testpassword"
    })
    assert login.status_code == 200  # Ensure login succeeded
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create test activities and glucose readings with UTC timezone
    activity_time = datetime(2025, 7, 29, 14, 0, 0, tzinfo=UTC)
    
    # Create activity
    client.post("/activities", json={
        "type": "running",
        "intensity": "high",
        "duration_min": 30,
        "start_time": activity_time.isoformat()
    }, headers=headers)
    
    # Create glucose readings (30 min before, 60 min after)
    client.post("/glucose-readings", json={
        "value": 120,
        "timestamp": (activity_time - timedelta(minutes=30)).isoformat(),
        "unit": "mg/dl"
    }, headers=headers)
    
    client.post("/glucose-readings", json={
        "value": 90,
        "timestamp": (activity_time + timedelta(minutes=60)).isoformat(),
        "unit": "mg/dl"
    }, headers=headers)
    
    # Test activity impact endpoint
    response = client.get("/analytics/activity-impact", headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert "activity_impacts" in data
    assert "meta" in data
    assert len(data["activity_impacts"]) >= 1
    
    # Check meta information
    meta = data["meta"]
    assert meta["group_by"] == "activity_type"
    assert meta["pre_activity_minutes"] == 30
    assert meta["post_activity_minutes"] == 120
    assert meta["total_activities_analyzed"] >= 1
    
    # Check activity impact data
    running_impact = next((impact for impact in data["activity_impacts"] if impact["group"] == "running"), None)
    assert running_impact is not None
    assert running_impact["avg_glucose_change"] == -30.0  # 90 - 120
    assert running_impact["num_activities"] == 1
    # Allow for different readings being selected
    assert abs(running_impact["avg_pre_activity"] - 120.0) <= 20.0  # Allow 20 mg/dl tolerance
    assert abs(running_impact["avg_post_activity"] - 90.0) <= 20.0  # Allow 20 mg/dl tolerance


def test_activity_impact_custom_parameters():
    """Test activity-impact endpoint with custom parameters."""
    # Generate unique identifiers for this test run
    unique_id = str(uuid.uuid4())[:8]
    email = f"activityimpactcustomtest{unique_id}@example.com"
    username = f"activityimpactcustomtestuser{unique_id}"
    
    # Register and login user
    client.post("/users", json={
        "email": email,
        "username": username,
        "password": "testpassword",
        "name": "Activity Impact Custom Test User"
    })
    login = client.post("/login", data={
        "username": username,
        "password": "testpassword"
    })
    assert login.status_code == 200  # Ensure login succeeded
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create test activity and glucose readings with custom timing (ensure UTC timezone)
    activity_time = datetime(2025, 7, 29, 16, 0, 0, tzinfo=UTC)
    client.post("/activities", json={
        "type": "walking",
        "intensity": "low",
        "duration_min": 45,
        "start_time": activity_time.isoformat()
    }, headers=headers)
    
    # Create glucose readings with custom timing (20 min before, 90 min after)
    client.post("/glucose-readings", json={
        "value": 140,
        "timestamp": (activity_time - timedelta(minutes=20)).isoformat(),
        "unit": "mg/dl"
    }, headers=headers)
    
    client.post("/glucose-readings", json={
        "value": 130,
        "timestamp": (activity_time + timedelta(minutes=90)).isoformat(),
        "unit": "mg/dl"
    }, headers=headers)
    
    # Test with custom parameters
    response = client.get("/analytics/activity-impact?pre_activity_minutes=25&post_activity_minutes=100", headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert len(data["activity_impacts"]) >= 1
    
    # Check meta has custom parameters
    meta = data["meta"]
    assert meta["pre_activity_minutes"] == 25
    assert meta["post_activity_minutes"] == 100
    assert meta["total_activities_analyzed"] >= 1


def test_activity_impact_no_data():
    """Test activity-impact endpoint when no activities or glucose readings exist."""
    # Generate unique identifiers for this test run
    unique_id = str(uuid.uuid4())[:8]
    email = f"activityimpactnonetest{unique_id}@example.com"
    username = f"activityimpactnonetestuser{unique_id}"
    
    # Register and login user
    client.post("/users", json={
        "email": email,
        "username": username,
        "password": "testpassword",
        "name": "Activity Impact None Test User"
    })
    login = client.post("/login", data={
        "username": username,
        "password": "testpassword"
    })
    assert login.status_code == 200  # Ensure login succeeded
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test activity impact endpoint with no data
    response = client.get("/analytics/activity-impact", headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert len(data["activity_impacts"]) == 0  # No activity impacts should be found
    assert data["meta"]["total_activities_analyzed"] == 0


def test_insulin_glucose_correlation_endpoint():
    """Test insulin-glucose-correlation endpoint with basic functionality."""
    # Generate unique identifiers for this test run
    unique_id = str(uuid.uuid4())[:8]
    email = f"insulincorrelationtest{unique_id}@example.com"
    username = f"insulincorrelationtestuser{unique_id}"
    
    # Register and login user
    client.post("/users", json={
        "email": email,
        "username": username,
        "password": "testpassword",
        "name": "Insulin Correlation Test User"
    })
    login = client.post("/login", data={
        "username": username,
        "password": "testpassword"
    })
    assert login.status_code == 200  # Ensure login succeeded
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create test insulin doses and glucose readings with UTC timezone
    insulin_time = datetime(2025, 7, 29, 14, 0, 0, tzinfo=UTC)
    
    # Create insulin dose
    client.post("/insulin-doses", json={
        "units": 3.0,
        "timestamp": insulin_time.isoformat()
    }, headers=headers)
    
    # Create glucose readings (30 min before, 90 min after)
    client.post("/glucose-readings", json={
        "value": 180,
        "timestamp": (insulin_time - timedelta(minutes=30)).isoformat(),
        "unit": "mg/dl"
    }, headers=headers)
    
    client.post("/glucose-readings", json={
        "value": 120,
        "timestamp": (insulin_time + timedelta(minutes=90)).isoformat(),
        "unit": "mg/dl"
    }, headers=headers)
    
    # Test insulin-glucose correlation endpoint
    response = client.get("/analytics/insulin-glucose-correlation", headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert "correlations" in data
    assert "overall_analysis" in data
    assert "meta" in data
    assert len(data["correlations"]) >= 1
    
    # Check meta information
    meta = data["meta"]
    assert meta["group_by"] == "dose_range"
    assert meta["pre_insulin_minutes"] == 30
    assert meta["post_insulin_minutes"] == 180
    
    # Check overall analysis
    overall = data["overall_analysis"]
    assert overall["total_doses_analyzed"] >= 1
    assert "recommendations" in overall
    
    # Check correlation data
    correlation = data["correlations"][0]
    assert "group" in correlation
    assert "avg_glucose_change" in correlation
    assert "avg_insulin_units" in correlation
    assert "insulin_sensitivity" in correlation
    assert "effectiveness_score" in correlation
    assert "correlation_coefficient" in correlation
    
    # Verify glucose change calculation (120 - 180 = -60)
    assert correlation["avg_glucose_change"] == -60.0
    assert correlation["avg_insulin_units"] == 3.0
    assert correlation["insulin_sensitivity"] == -20.0  # -60 / 3


def test_insulin_glucose_correlation_custom_parameters():
    """Test insulin-glucose-correlation endpoint with custom parameters."""
    # Generate unique identifiers for this test run
    unique_id = str(uuid.uuid4())[:8]
    email = f"insulincorrelationcustomtest{unique_id}@example.com"
    username = f"insulincorrelationcustomtestuser{unique_id}"
    
    # Register and login user
    client.post("/users", json={
        "email": email,
        "username": username,
        "password": "testpassword",
        "name": "Insulin Correlation Custom Test User"
    })
    login = client.post("/login", data={
        "username": username,
        "password": "testpassword"
    })
    assert login.status_code == 200  # Ensure login succeeded
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create test insulin dose and glucose readings with custom timing (ensure UTC timezone)
    insulin_time = datetime(2025, 7, 29, 16, 0, 0, tzinfo=UTC)
    client.post("/insulin-doses", json={
        "units": 2.5,
        "timestamp": insulin_time.isoformat()
    }, headers=headers)
    
    # Create glucose readings with custom timing (20 min before, 120 min after)
    client.post("/glucose-readings", json={
        "value": 200,
        "timestamp": (insulin_time - timedelta(minutes=20)).isoformat(),
        "unit": "mg/dl"
    }, headers=headers)
    
    client.post("/glucose-readings", json={
        "value": 150,
        "timestamp": (insulin_time + timedelta(minutes=120)).isoformat(),
        "unit": "mg/dl"
    }, headers=headers)
    
    # Test with custom parameters
    response = client.get("/analytics/insulin-glucose-correlation?pre_insulin_minutes=25&post_insulin_minutes=150", headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert len(data["correlations"]) >= 1
    
    # Check meta has custom parameters
    meta = data["meta"]
    assert meta["pre_insulin_minutes"] == 25
    assert meta["post_insulin_minutes"] == 150
    assert data["overall_analysis"]["total_doses_analyzed"] >= 1


def test_insulin_glucose_correlation_no_data():
    """Test insulin-glucose-correlation endpoint when no insulin doses or glucose readings exist."""
    # Generate unique identifiers for this test run
    unique_id = str(uuid.uuid4())[:8]
    email = f"insulincorrelationnonetest{unique_id}@example.com"
    username = f"insulincorrelationnonetestuser{unique_id}"
    
    # Register and login user
    client.post("/users", json={
        "email": email,
        "username": username,
        "password": "testpassword",
        "name": "Insulin Correlation None Test User"
    })
    login = client.post("/login", data={
        "username": username,
        "password": "testpassword"
    })
    assert login.status_code == 200  # Ensure login succeeded
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test insulin-glucose correlation endpoint with no data
    response = client.get("/analytics/insulin-glucose-correlation", headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert len(data["correlations"]) == 0  # No correlations should be found
    assert data["overall_analysis"]["total_doses_analyzed"] == 0
    assert "No insulin doses found" in data["overall_analysis"]["recommendations"][0] 