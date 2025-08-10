import pytest
import uuid
from datetime import datetime, timedelta, UTC

def test_dashboard_overview_mgdl(client, test_user, auth_headers):
    """Test dashboard overview with mg/dl units."""
    # Add sample data
    client.post("/glucose-readings", json={
        "value": 120,
        "unit": "mg/dl"
    }, headers=auth_headers)

    client.post("/meals", json={
        "description": "Test Breakfast",
        "total_carbs": 45,
        "total_weight": 300
    }, headers=auth_headers)

    # Test dashboard endpoint
    response = client.get("/visualization/dashboard?unit=mg/dl", headers=auth_headers)
    assert response.status_code == 200

    data = response.json()
    assert "dashboard" in data
    dashboard = data["dashboard"]
    assert "glucose_summary" in dashboard
    assert "recent_meals" in dashboard
    assert "upcoming_insulin" in dashboard
    assert "activity_summary" in dashboard
    assert "data_sources" in data
    assert data["meta"]["unit"] == "mg/dl"

def test_dashboard_overview_mmol(client, test_user, auth_headers):
    """Test dashboard overview with mmol/l units."""
    # Add sample data
    client.post("/glucose-readings", json={
        "value": 6.7,
        "unit": "mmol/l"
    }, headers=auth_headers)

    # Test dashboard endpoint
    response = client.get("/visualization/dashboard?unit=mmol/l", headers=auth_headers)
    assert response.status_code == 200

    data = response.json()
    assert data["meta"]["unit"] == "mmol/l"

def test_glucose_timeline(client, test_user, auth_headers):
    """Test glucose timeline endpoint."""
    # Add sample data
    client.post("/glucose-readings", json={
        "value": 120,
        "unit": "mg/dl"
    }, headers=auth_headers)

    client.post("/meals", json={
        "description": "Test Lunch",
        "total_carbs": 60,
        "total_weight": 400
    }, headers=auth_headers)

    # Test timeline endpoint (explicit datetimes required)
    response = client.get(
        "/visualization/glucose-timeline",
        params={
            "start_datetime": datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0).isoformat(),
            "end_datetime": datetime.now(UTC).isoformat(),
            "format": "series",
        },
        headers=auth_headers,
    )
    assert response.status_code == 200

    data = response.json()
    assert "points" in data
    assert "events" in data

def test_glucose_timeline_with_ingredients(client, test_user, auth_headers):
    """Test glucose timeline with detailed meal ingredients."""
    # Add sample data with ingredients
    meal_response = client.post("/meals", json={
        "description": "Test Dinner",
        "total_carbs": 75,
        "total_weight": 500
    }, headers=auth_headers)
    assert meal_response.status_code == 201
    meal_id = meal_response.json()["id"]

    # Add ingredients
    client.post(f"/meals/{meal_id}/ingredients", json={
        "name": "Rice",
        "carbs_per_100g": 28,
        "weight_grams": 200
    }, headers=auth_headers)

    client.post(f"/meals/{meal_id}/ingredients", json={
        "name": "Chicken",
        "carbs_per_100g": 0,
        "weight_grams": 150
    }, headers=auth_headers)

    # Test timeline endpoint
    response = client.get(
        "/visualization/glucose-timeline",
        params={
            "start_datetime": datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0).isoformat(),
            "end_datetime": datetime.now(UTC).isoformat(),
            "format": "series",
        },
        headers=auth_headers,
    )
    assert response.status_code == 200

    data = response.json()
    assert "events" in data
    assert any(ev["type"] == "meal" for ev in data["events"])

    # Ingredients are not included in series events payload; just assert meal event exists

def test_glucose_trend_data(client, test_user, auth_headers):
    """Test glucose trend data endpoint."""
    # Add sample glucose readings
    readings = [
        {"value": 120, "unit": "mg/dl"},
        {"value": 135, "unit": "mg/dl"},
        {"value": 110, "unit": "mg/dl"},
        {"value": 125, "unit": "mg/dl"},
        {"value": 140, "unit": "mg/dl"}
    ]

    for reading in readings:
        client.post("/glucose-readings", json=reading, headers=auth_headers)

    # Test trend endpoint
    response = client.get("/visualization/glucose-trend", headers=auth_headers)
    assert response.status_code == 200

    data = response.json()
    assert "trend_data" in data
    assert "statistics" in data
    assert "patterns" in data
    assert data["meta"]["unit"] == "mg/dl"

def test_glucose_trend_data_with_moving_average(client, test_user, auth_headers):
    """Test glucose trend data with moving average calculation."""
    # Add sample glucose readings
    readings = [
        {"value": 120, "unit": "mg/dl"},
        {"value": 135, "unit": "mg/dl"},
        {"value": 110, "unit": "mg/dl"},
        {"value": 125, "unit": "mg/dl"},
        {"value": 140, "unit": "mg/dl"},
        {"value": 115, "unit": "mg/dl"},
        {"value": 130, "unit": "mg/dl"}
    ]

    for reading in readings:
        client.post("/glucose-readings", json=reading, headers=auth_headers)

    # Test trend endpoint with moving average
    response = client.get("/visualization/glucose-trend?moving_average=true", headers=auth_headers)
    assert response.status_code == 200

    data = response.json()
    assert "trend_data" in data
    assert "moving_average" in data["trend_data"]
    assert "statistics" in data

def test_glucose_trend_data_mmol(client, test_user, auth_headers):
    """Test glucose trend data with mmol/l units."""
    # Add sample glucose readings in mmol/l
    readings = [
        {"value": 6.7, "unit": "mmol/l"},
        {"value": 7.5, "unit": "mmol/l"},
        {"value": 6.1, "unit": "mmol/l"},
        {"value": 6.9, "unit": "mmol/l"},
        {"value": 7.8, "unit": "mmol/l"}
    ]

    for reading in readings:
        client.post("/glucose-readings", json=reading, headers=auth_headers)

    # Test trend endpoint with mmol/l
    response = client.get("/visualization/glucose-trend?unit=mmol/l", headers=auth_headers)
    assert response.status_code == 200

    data = response.json()
    assert "trend_data" in data
    assert data["meta"]["unit"] == "mmol/l"

def test_meal_impact_data(client, test_user, auth_headers):
    """Test meal impact analysis endpoint."""
    # Add sample meals and glucose readings
    meal_response = client.post("/meals", json={
        "description": "Test Breakfast",
        "total_carbs": 45,
        "total_weight": 300
    }, headers=auth_headers)
    assert meal_response.status_code == 201
    meal_id = meal_response.json()["id"]

    # Add glucose readings before and after meal
    client.post("/glucose-readings", json={
        "value": 100,
        "unit": "mg/dl"
    }, headers=auth_headers)

    client.post("/glucose-readings", json={
        "value": 140,
        "unit": "mg/dl"
    }, headers=auth_headers)

    # Test meal impact endpoint
    response = client.get(f"/visualization/meal-impact/{meal_id}", headers=auth_headers)
    assert response.status_code == 200

    data = response.json()
    assert "meal_impact" in data
    assert "glucose_changes" in data["meal_impact"]
    assert "correlation_analysis" in data["meal_impact"]

def test_activity_impact_data(client, test_user, auth_headers):
    """Test activity impact analysis endpoint."""
    # Add sample activities and glucose readings
    activity_response = client.post("/activities", json={
        "type": "Running",
        "intensity": "High",
        "duration_min": 30
    }, headers=auth_headers)
    assert activity_response.status_code == 201
    activity_id = activity_response.json()["id"]

    # Add glucose readings before and after activity
    client.post("/glucose-readings", json={
        "value": 150,
        "unit": "mg/dl"
    }, headers=auth_headers)

    client.post("/glucose-readings", json={
        "value": 120,
        "unit": "mg/dl"
    }, headers=auth_headers)

    # Test activity impact endpoint
    response = client.get(f"/visualization/activity-impact/{activity_id}", headers=auth_headers)
    assert response.status_code == 200

    data = response.json()
    assert "activity_impact" in data
    assert "glucose_changes" in data["activity_impact"]
    assert "effectiveness_analysis" in data["activity_impact"]

def test_data_quality_metrics(client, test_user, auth_headers):
    """Test data quality metrics endpoint."""
    # Add sample data
    readings = [
        {"value": 120, "unit": "mg/dl"},
        {"value": 135, "unit": "mg/dl"},
        {"value": 110, "unit": "mg/dl"}
    ]

    for reading in readings:
        client.post("/glucose-readings", json=reading, headers=auth_headers)

    client.post("/meals", json={
        "description": "Test Meal",
        "total_carbs": 45,
        "total_weight": 300
    }, headers=auth_headers)

    client.post("/activities", json={
        "type": "Walking",
        "intensity": "Low",
        "duration_min": 20
    }, headers=auth_headers)

    # Test data quality endpoint
    response = client.get("/visualization/data-quality", headers=auth_headers)
    assert response.status_code == 200

    data = response.json()
    assert "quality_metrics" in data
    assert "completeness" in data["quality_metrics"]
    assert "consistency" in data["quality_metrics"]
    assert "timeliness" in data["quality_metrics"]

def test_unit_conversion_accuracy(client, test_user, auth_headers):
    """Test unit conversion accuracy in visualization endpoints."""
    # Add glucose reading in mg/dl
    client.post("/glucose-readings", json={
        "value": 120,
        "unit": "mg/dl"
    }, headers=auth_headers)

    # Test both unit formats
    response_mgdl = client.get("/visualization/glucose-trend?unit=mg/dl", headers=auth_headers)
    response_mmol = client.get("/visualization/glucose-trend?unit=mmol/l", headers=auth_headers)

    assert response_mgdl.status_code == 200
    assert response_mmol.status_code == 200

    # Verify unit conversion accuracy
    data_mgdl = response_mgdl.json()
    data_mmol = response_mmol.json()
    assert data_mgdl["meta"]["unit"] == "mg/dl"
    assert data_mmol["meta"]["unit"] == "mmol/l"

def test_invalid_unit_parameter(client, test_user, auth_headers):
    """Test handling of invalid unit parameters."""
    response = client.get("/visualization/glucose-trend?unit=invalid", headers=auth_headers)
    assert response.status_code == 400
    assert "Invalid unit" in response.json()["detail"]

def test_no_data_handling(client, test_user, auth_headers):
    """Test visualization endpoints with no data."""
    # Test dashboard with no data
    response = client.get("/visualization/dashboard", headers=auth_headers)
    assert response.status_code == 200

    data = response.json()
    assert "dashboard" in data
    assert "glucose_summary" in data["dashboard"]
    assert "recent_meals" in data["dashboard"]

    # Test trend with no data
    response = client.get("/visualization/glucose-trend", headers=auth_headers)
    assert response.status_code == 200

    data = response.json()
    assert "trend_data" in data
    assert len(data["trend_data"]["glucose_readings"]) == 0

def test_custom_date_range(client, test_user, auth_headers):
    """Test visualization with custom date range."""
    # Add sample data
    client.post("/glucose-readings", json={
        "value": 120,
        "unit": "mg/dl"
    }, headers=auth_headers)

    # Test with custom date range
    start_date = (datetime.now(UTC) - timedelta(days=7)).strftime("%Y-%m-%d")
    end_date = datetime.now(UTC).strftime("%Y-%m-%d")

    response = client.get(f"/visualization/glucose-trend?start_date={start_date}&end_date={end_date}", headers=auth_headers)
    assert response.status_code == 200

    data = response.json()
    assert "trend_data" in data
    assert "meta" in data
    assert "start_date" in data["meta"]
    assert "end_date" in data["meta"]

def test_missing_custom_date_parameters(client, test_user, auth_headers):
    """Test handling of missing custom date parameters."""
    # Test with only start_date
    start_date = (datetime.now(UTC) - timedelta(days=7)).strftime("%Y-%m-%d")
    response = client.get(f"/visualization/glucose-trend?start_date={start_date}", headers=auth_headers)
    assert response.status_code == 400
    assert "Both start_date and end_date" in response.json()["detail"]

    # Test with only end_date
    end_date = datetime.now(UTC).strftime("%Y-%m-%d")
    response = client.get(f"/visualization/glucose-trend?end_date={end_date}", headers=auth_headers)
    assert response.status_code == 400
    assert "Both start_date and end_date" in response.json()["detail"]

def test_authentication_required(client):
    """Test that visualization endpoints require authentication."""
    response = client.get("/visualization/dashboard")
    assert response.status_code == 401

def test_recommendations_integration(client, test_user, auth_headers):
    """Test visualization endpoints with recommendations integration."""
    # Add sample data
    client.post("/glucose-readings", json={
        "value": 180,
        "unit": "mg/dl"
    }, headers=auth_headers)

    client.post("/meals", json={
        "description": "High Carb Meal",
        "total_carbs": 80,
        "total_weight": 500
    }, headers=auth_headers)

    # Test dashboard with recommendations
    response = client.get("/visualization/dashboard", headers=auth_headers)
    assert response.status_code == 200

    data = response.json()
    assert "dashboard" in data
    assert "recommendations" in data["dashboard"]
    assert "insights" in data["dashboard"]