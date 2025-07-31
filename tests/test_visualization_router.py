import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select
from app.main import app
from app.core.database import get_session
from app.models.user import User
from app.models.glucose_reading import GlucoseReading
from app.models.meal import Meal
from app.models.activity import Activity
from app.models.insulin_dose import InsulinDose
from app.models.meal_ingredient import MealIngredient
from datetime import datetime, timedelta, UTC
import uuid

client = TestClient(app)

def get_test_session():
    """Override get_session for testing."""
    from app.core.database import engine
    with Session(engine) as session:
        yield session

app.dependency_overrides[get_session] = get_test_session

@pytest.fixture
def test_user(session: Session):
    """Create a test user."""
    user = User(
        email=f"test_{uuid.uuid4().hex[:8]}@example.com",
        name="Test User",
        username=f"testuser_{uuid.uuid4().hex[:8]}",
        hashed_password="hashed_password"
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

@pytest.fixture
def auth_headers(test_user):
    """Get authentication headers for the test user."""
    # Create user first
    response = client.post("/users", json={
        "email": test_user.email,
        "name": test_user.name,
        "username": test_user.username,
        "password": "testpassword"
    })
    
    # Login to get token
    response = client.post("/login", data={
        "username": test_user.username,
        "password": "testpassword"
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def sample_data(session: Session, test_user):
    """Create sample data for testing."""
    # Create glucose readings (mix of mg/dl and mmol/l)
    glucose_readings = [
        GlucoseReading(
            user_id=test_user.id,
            value=120.0,
            unit="mg/dl",
            timestamp=datetime.now(UTC) - timedelta(hours=2),
            note="Manual entry"
        ),
        GlucoseReading(
            user_id=test_user.id,
            value=6.7,
            unit="mmol/l",
            timestamp=datetime.now(UTC) - timedelta(hours=1),
            note="CSV upload"
        ),
        GlucoseReading(
            user_id=test_user.id,
            value=140.0,
            unit="mg/dl",
            timestamp=datetime.now(UTC),
            note="Manual entry"
        )
    ]
    
    # Create a meal with ingredients
    meal = Meal(
        user_id=test_user.id,
        description="Breakfast",
        total_carbs=45.0,
        total_weight=250.0,
        timestamp=datetime.now(UTC) - timedelta(hours=1, minutes=30),
        photo_url="https://example.com/breakfast.jpg"
    )
    session.add(meal)
    session.commit()
    session.refresh(meal)
    
    ingredients = [
        MealIngredient(
            meal_id=meal.id,
            name="Oatmeal",
            carbs=30.0,
            weight=100.0
        ),
        MealIngredient(
            meal_id=meal.id,
            name="Banana",
            carbs=15.0,
            weight=150.0
        )
    ]
    
    # Create activity
    activity = Activity(
        user_id=test_user.id,
        type="walking",
        intensity="moderate",
        duration_min=30,
        calories_burned=150.0,
        timestamp=datetime.now(UTC) - timedelta(minutes=30)
    )
    
    # Create insulin dose
    insulin_dose = InsulinDose(
        user_id=test_user.id,
        units=5.0,
        type="rapid_acting",
        related_meal_id=meal.id,
        timestamp=datetime.now(UTC) - timedelta(hours=1, minutes=15)
    )
    
    # Add all data to session
    for reading in glucose_readings:
        session.add(reading)
    for ingredient in ingredients:
        session.add(ingredient)
    session.add(activity)
    session.add(insulin_dose)
    session.commit()
    
    return {
        "glucose_readings": glucose_readings,
        "meal": meal,
        "ingredients": ingredients,
        "activity": activity,
        "insulin_dose": insulin_dose
    }

def test_dashboard_overview_mgdl(auth_headers, sample_data):
    """Test dashboard overview with mg/dl units."""
    response = client.get("/visualization/dashboard?window=day&unit=mg/dl", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    
    # Check structure
    assert "dashboard" in data
    assert "data_sources" in data
    assert "meta" in data
    
    # Check glucose summary
    glucose_summary = data["dashboard"]["glucose_summary"]
    assert glucose_summary["unit"] == "mg/dl"
    assert glucose_summary["current_value"] is not None
    assert "trend" in glucose_summary
    assert "last_reading_time" in glucose_summary
    
    # Check data sources
    sources = data["data_sources"]
    assert sources["glucose_readings"]["total_count"] == 3
    assert sources["glucose_readings"]["csv_uploaded"] == 1
    assert sources["glucose_readings"]["manual_entries"] == 2

def test_dashboard_overview_mmol(auth_headers, sample_data):
    """Test dashboard overview with mmol/l units."""
    response = client.get("/visualization/dashboard?window=day&unit=mmol/l", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    
    # Check glucose summary is in mmol/l
    glucose_summary = data["dashboard"]["glucose_summary"]
    assert glucose_summary["unit"] == "mmol/l"
    assert glucose_summary["current_value"] is not None
    
    # Check that values are converted (140 mg/dl should be ~7.8 mmol/l)
    assert 7.0 <= glucose_summary["current_value"] <= 8.5

def test_glucose_timeline(auth_headers, sample_data):
    """Test glucose timeline endpoint."""
    response = client.get("/visualization/glucose-timeline?window=day&unit=mg/dl", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    
    # Check structure
    assert "timeline" in data
    assert "glucose_readings" in data["timeline"]
    assert "events" in data["timeline"]
    assert "meta" in data
    
    # Check glucose readings
    readings = data["timeline"]["glucose_readings"]
    assert len(readings) == 3
    
    # Check events
    events = data["timeline"]["events"]
    assert len(events) >= 3  # meal, activity, insulin dose
    
    # Check event types
    event_types = [event["type"] for event in events]
    assert "meal" in event_types
    assert "activity" in event_types
    assert "insulin_dose" in event_types

def test_glucose_timeline_with_ingredients(auth_headers, sample_data):
    """Test glucose timeline with meal ingredients."""
    response = client.get("/visualization/glucose-timeline?window=day&include_ingredients=true", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    
    # Find meal event with ingredients
    meal_events = [event for event in data["timeline"]["events"] if event["type"] == "meal"]
    assert len(meal_events) > 0
    
    meal_event = meal_events[0]
    assert "ingredients" in meal_event
    assert len(meal_event["ingredients"]) == 2
    assert meal_event["ingredients"][0]["name"] == "Oatmeal"
    assert meal_event["ingredients"][1]["name"] == "Banana"

def test_glucose_trend_data(auth_headers, sample_data):
    """Test glucose trend data endpoint."""
    response = client.get("/visualization/glucose-trend-data?window=day&unit=mg/dl", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    
    # Check clean data structure
    assert "timestamps" in data
    assert "glucose_values" in data
    assert "moving_average" in data
    assert "meta" in data
    
    # Check data arrays
    assert len(data["timestamps"]) == 3
    assert len(data["glucose_values"]) == 3
    assert data["meta"]["unit"] == "mg/dl"

def test_glucose_trend_data_with_moving_average(auth_headers, sample_data):
    """Test glucose trend data with moving average."""
    response = client.get("/visualization/glucose-trend-data?window=day&include_moving_average=true&moving_avg_window=3", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    
    # Check that moving average is calculated
    assert len(data["moving_average"]) > 0
    assert data["meta"]["moving_avg_window"] == 3

def test_glucose_trend_data_mmol(auth_headers, sample_data):
    """Test glucose trend data with mmol/l units."""
    response = client.get("/visualization/glucose-trend-data?window=day&unit=mmol/l", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    
    # Check that values are converted to mmol/l
    assert data["meta"]["unit"] == "mmol/l"
    values = data["glucose_values"]
    assert all(3.0 <= value <= 10.0 for value in values)  # Reasonable mmol/l range

def test_meal_impact_data(auth_headers, sample_data):
    """Test meal impact data endpoint."""
    response = client.get("/visualization/meal-impact-data?window=day&unit=mg/dl", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    
    # Check structure
    assert "meal_impacts" in data
    assert "meta" in data
    assert data["meta"]["unit"] == "mg/dl"
    
    # Check meal impacts data
    impacts = data["meal_impacts"]
    if impacts:  # If there are meals with glucose data
        impact = impacts[0]
        assert "group" in impact
        assert "avg_glucose_change" in impact
        assert "num_meals" in impact

def test_activity_impact_data(auth_headers, sample_data):
    """Test activity impact data endpoint."""
    response = client.get("/visualization/activity-impact-data?window=day&unit=mg/dl", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    
    # Check structure
    assert "activity_impacts" in data
    assert "meta" in data
    assert data["meta"]["unit"] == "mg/dl"
    
    # Check activity impacts data
    impacts = data["activity_impacts"]
    if impacts:  # If there are activities with glucose data
        impact = impacts[0]
        assert "group" in impact
        assert "avg_glucose_change" in impact
        assert "num_activities" in impact
        assert "avg_calories_burned" in impact

def test_data_quality_metrics(auth_headers, sample_data):
    """Test data quality metrics endpoint."""
    response = client.get("/visualization/data-quality?window=day", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    
    # Check structure
    assert "data_quality" in data
    assert "recommendations" in data
    assert "meta" in data
    
    # Check glucose readings quality
    glucose_quality = data["data_quality"]["glucose_readings"]
    assert glucose_quality["total"] == 3
    assert glucose_quality["csv_uploaded"] == 1
    assert glucose_quality["manual_entries"] == 2
    assert "coverage_percentage" in glucose_quality
    
    # Check meals quality
    meals_quality = data["data_quality"]["meals"]
    assert meals_quality["total"] == 1
    assert meals_quality["with_ingredients"] == 1
    assert meals_quality["with_photos"] == 1
    
    # Check activities quality
    activities_quality = data["data_quality"]["activities"]
    assert activities_quality["total"] == 1
    assert activities_quality["with_calorie_calculations"] == 1
    
    # Check insulin quality
    insulin_quality = data["data_quality"]["insulin_doses"]
    assert insulin_quality["total"] == 1
    assert insulin_quality["with_meal_relationships"] == 1

def test_unit_conversion_accuracy():
    """Test unit conversion accuracy."""
    from app.routers.visualization_router import convert_glucose_value
    
    # Test mg/dl to mmol/l
    assert convert_glucose_value(180, "mg/dl", "mmol/l") == 10.0
    assert convert_glucose_value(90, "mg/dl", "mmol/l") == 5.0
    
    # Test mmol/l to mg/dl
    assert convert_glucose_value(10.0, "mmol/l", "mg/dl") == 180
    assert convert_glucose_value(5.0, "mmol/l", "mg/dl") == 90
    
    # Test same unit
    assert convert_glucose_value(120, "mg/dl", "mg/dl") == 120
    assert convert_glucose_value(6.7, "mmol/l", "mmol/l") == 6.7

def test_invalid_unit_parameter(auth_headers):
    """Test invalid unit parameter handling."""
    response = client.get("/visualization/dashboard?unit=invalid_unit", headers=auth_headers)
    assert response.status_code == 400
    assert "Unit must be 'mg/dl' or 'mmol/l'" in response.json()["detail"]

def test_no_data_handling(auth_headers, test_user):
    """Test handling of users with no data."""
    response = client.get("/visualization/dashboard?window=day", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    
    # Check that dashboard handles no data gracefully
    glucose_summary = data["dashboard"]["glucose_summary"]
    assert glucose_summary["current_value"] is None
    assert glucose_summary["trend"] == "no_data"
    
    # Check data sources show zero counts
    sources = data["data_sources"]
    assert sources["glucose_readings"]["total_count"] == 0
    assert sources["meals"]["total_count"] == 0
    assert sources["activities"]["total_count"] == 0
    assert sources["insulin_doses"]["total_count"] == 0

def test_custom_date_range(auth_headers, sample_data):
    """Test custom date range functionality."""
    start_date = (datetime.now(UTC) - timedelta(days=7)).strftime("%Y-%m-%d")
    end_date = datetime.now(UTC).strftime("%Y-%m-%d")
    
    response = client.get(f"/visualization/dashboard?window=custom&start_date={start_date}&end_date={end_date}", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    
    # Check that custom date range works
    assert "dashboard" in data
    assert "meta" in data

def test_missing_custom_date_parameters(auth_headers):
    """Test error handling for missing custom date parameters."""
    response = client.get("/visualization/dashboard?window=custom", headers=auth_headers)
    assert response.status_code == 400
    assert "start_date and end_date are required" in response.json()["detail"]

def test_authentication_required():
    """Test that authentication is required for all endpoints."""
    endpoints = [
        "/visualization/dashboard",
        "/visualization/glucose-timeline",
        "/visualization/glucose-trend-data",
        "/visualization/meal-impact-data",
        "/visualization/activity-impact-data",
        "/visualization/data-quality"
    ]
    
    for endpoint in endpoints:
        response = client.get(endpoint)
        assert response.status_code == 401

def test_recommendations_integration(auth_headers, sample_data):
    """Test that visualization endpoints work with AI recommendations."""
    # First get recommendations
    response = client.get("/analytics/recommendations?window=day", headers=auth_headers)
    assert response.status_code == 200
    recommendations = response.json()
    
    # Then get dashboard data
    response = client.get("/visualization/dashboard?window=day", headers=auth_headers)
    assert response.status_code == 200
    dashboard = response.json()
    
    # Both should work together and use the same data
    assert dashboard["data_sources"]["glucose_readings"]["total_count"] == 3
    assert recommendations["summary"]["total_glucose_readings"] == 3 