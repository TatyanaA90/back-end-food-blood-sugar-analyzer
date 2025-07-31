import pytest
import uuid
from datetime import datetime, timedelta, UTC
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_dashboard_overview_mgdl():
    """Test dashboard overview with mg/dl units."""
    # Generate unique identifiers for this test run
    unique_id = str(uuid.uuid4())[:8]
    email = f"dashboardtest{unique_id}@example.com"
    username = f"dashboardtestuser{unique_id}"
    
    # Register and login user
    client.post("/users", json={
        "email": email,
        "username": username,
        "password": "testpassword",
        "name": "Dashboard Test User"
    })
    login = client.post("/login", data={
        "username": username,
        "password": "testpassword"
    })
    assert login.status_code == 200
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Add sample data
    client.post("/glucose-readings", json={
        "value": 120,
        "unit": "mg/dl"
    }, headers=headers)
    
    client.post("/meals", json={
        "description": "Test Breakfast",
        "total_carbs": 45,
        "total_weight": 300
    }, headers=headers)
    
    # Test dashboard endpoint
    response = client.get("/visualization/dashboard?unit=mg/dl", headers=headers)
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

def test_dashboard_overview_mmol():
    """Test dashboard overview with mmol/l units."""
    # Generate unique identifiers for this test run
    unique_id = str(uuid.uuid4())[:8]
    email = f"dashboardmmoltest{unique_id}@example.com"
    username = f"dashboardmmoltestuser{unique_id}"
    
    # Register and login user
    client.post("/users", json={
        "email": email,
        "username": username,
        "password": "testpassword",
        "name": "Dashboard mmol Test User"
    })
    login = client.post("/login", data={
        "username": username,
        "password": "testpassword"
    })
    assert login.status_code == 200
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Add sample data
    client.post("/glucose-readings", json={
        "value": 6.7,
        "unit": "mmol/l"
    }, headers=headers)
    
    # Test dashboard endpoint
    response = client.get("/visualization/dashboard?unit=mmol/l", headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["meta"]["unit"] == "mmol/l"

def test_glucose_timeline():
    """Test glucose timeline endpoint."""
    # Generate unique identifiers for this test run
    unique_id = str(uuid.uuid4())[:8]
    email = f"timelinetest{unique_id}@example.com"
    username = f"timelinetestuser{unique_id}"
    
    # Register and login user
    client.post("/users", json={
        "email": email,
        "username": username,
        "password": "testpassword",
        "name": "Timeline Test User"
    })
    login = client.post("/login", data={
        "username": username,
        "password": "testpassword"
    })
    assert login.status_code == 200
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Add sample data
    client.post("/glucose-readings", json={
        "value": 120,
        "unit": "mg/dl"
    }, headers=headers)
    
    client.post("/meals", json={
        "description": "Test Meal",
        "total_carbs": 45,
        "total_weight": 300
    }, headers=headers)
    
    # Test timeline endpoint
    response = client.get("/visualization/glucose-timeline?window=day&unit=mg/dl", headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert "glucose_readings" in data
    assert "events" in data
    assert "meta" in data

def test_glucose_timeline_with_ingredients():
    """Test glucose timeline with meal ingredients."""
    # Generate unique identifiers for this test run
    unique_id = str(uuid.uuid4())[:8]
    email = f"timelineingtest{unique_id}@example.com"
    username = f"timelineingtestuser{unique_id}"
    
    # Register and login user
    client.post("/users", json={
        "email": email,
        "username": username,
        "password": "testpassword",
        "name": "Timeline Ingredients Test User"
    })
    login = client.post("/login", data={
        "username": username,
        "password": "testpassword"
    })
    assert login.status_code == 200
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Add sample data
    client.post("/glucose-readings", json={
        "value": 120,
        "unit": "mg/dl"
    }, headers=headers)
    
    meal_response = client.post("/meals", json={
        "description": "Test Meal with Ingredients",
        "total_carbs": 45.0,
        "total_weight": 300.0,
        "ingredients": [
            {
                "name": "Oatmeal",
                "carbs": 30.0,
                "weight": 100.0
            },
            {
                "name": "Banana",
                "carbs": 15.0,
                "weight": 200.0
            }
        ]
    }, headers=headers)
    assert meal_response.status_code == 201
    
    # Test timeline with ingredients
    response = client.get("/visualization/glucose-timeline?window=day&include_ingredients=true", headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert "glucose_readings" in data
    assert "events" in data

def test_glucose_trend_data():
    """Test glucose trend data endpoint."""
    # Generate unique identifiers for this test run
    unique_id = str(uuid.uuid4())[:8]
    email = f"trendtest{unique_id}@example.com"
    username = f"trendtestuser{unique_id}"
    
    # Register and login user
    client.post("/users", json={
        "email": email,
        "username": username,
        "password": "testpassword",
        "name": "Trend Test User"
    })
    login = client.post("/login", data={
        "username": username,
        "password": "testpassword"
    })
    assert login.status_code == 200
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Add sample data
    client.post("/glucose-readings", json={
        "value": 120,
        "unit": "mg/dl"
    }, headers=headers)
    
    client.post("/glucose-readings", json={
        "value": 140,
        "unit": "mg/dl"
    }, headers=headers)
    
    client.post("/glucose-readings", json={
        "value": 130,
        "unit": "mg/dl"
    }, headers=headers)
    
    # Test trend data endpoint
    response = client.get("/visualization/glucose-trend-data?window=day&unit=mg/dl", headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert "timestamps" in data
    assert "glucose_values" in data
    assert "moving_average" in data
    assert "meta" in data
    assert data["meta"]["unit"] == "mg/dl"

def test_glucose_trend_data_with_moving_average():
    """Test glucose trend data with moving average."""
    # Generate unique identifiers for this test run
    unique_id = str(uuid.uuid4())[:8]
    email = f"trendavgtest{unique_id}@example.com"
    username = f"trendavgtestuser{unique_id}"
    
    # Register and login user
    client.post("/users", json={
        "email": email,
        "username": username,
        "password": "testpassword",
        "name": "Trend Average Test User"
    })
    login = client.post("/login", data={
        "username": username,
        "password": "testpassword"
    })
    assert login.status_code == 200
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Add sample data
    for i in range(5):
        client.post("/glucose-readings", json={
            "value": 120 + i * 10,
            "unit": "mg/dl"
        }, headers=headers)
    
    # Test trend data with moving average
    response = client.get("/visualization/glucose-trend-data?window=day&include_moving_average=true&moving_avg_window=3", headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert len(data["moving_average"]) > 0
    assert data["meta"]["moving_avg_window"] == 3

def test_glucose_trend_data_mmol():
    """Test glucose trend data with mmol/l units."""
    # Generate unique identifiers for this test run
    unique_id = str(uuid.uuid4())[:8]
    email = f"trendmmoltest{unique_id}@example.com"
    username = f"trendmmoltestuser{unique_id}"
    
    # Register and login user
    client.post("/users", json={
        "email": email,
        "username": username,
        "password": "testpassword",
        "name": "Trend mmol Test User"
    })
    login = client.post("/login", data={
        "username": username,
        "password": "testpassword"
    })
    assert login.status_code == 200
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Add sample data
    client.post("/glucose-readings", json={
        "value": 6.7,
        "unit": "mmol/l"
    }, headers=headers)
    
    # Test trend data with mmol/l
    response = client.get("/visualization/glucose-trend-data?window=day&unit=mmol/l", headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["meta"]["unit"] == "mmol/l"
    values = data["glucose_values"]
    assert all(3.0 <= value <= 10.0 for value in values)  # Reasonable mmol/l range

def test_meal_impact_data():
    """Test meal impact data endpoint."""
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
    assert login.status_code == 200
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Add sample data
    client.post("/glucose-readings", json={
        "value": 120,
        "unit": "mg/dl"
    }, headers=headers)
    
    client.post("/meals", json={
        "description": "Breakfast",
        "total_carbs": 45,
        "total_weight": 300
    }, headers=headers)
    
    # Test meal impact data
    response = client.get("/visualization/meal-impact-data?window=day&unit=mg/dl", headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert "meal_impacts" in data
    assert "meta" in data
    assert data["meta"]["unit"] == "mg/dl"

def test_activity_impact_data():
    """Test activity impact data endpoint."""
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
    assert login.status_code == 200
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Add sample data
    client.post("/glucose-readings", json={
        "value": 120,
        "unit": "mg/dl"
    }, headers=headers)
    
    client.post("/activities", json={
        "type": "running",
        "duration_min": 30,
        "intensity": "moderate"
    }, headers=headers)
    
    # Test activity impact data
    response = client.get("/visualization/activity-impact-data?window=day&unit=mg/dl", headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert "activity_impacts" in data
    assert "meta" in data
    assert data["meta"]["unit"] == "mg/dl"

def test_data_quality_metrics():
    """Test data quality metrics endpoint."""
    # Generate unique identifiers for this test run
    unique_id = str(uuid.uuid4())[:8]
    email = f"dataqualitytest{unique_id}@example.com"
    username = f"dataqualitytestuser{unique_id}"
    
    # Register and login user
    client.post("/users", json={
        "email": email,
        "username": username,
        "password": "testpassword",
        "name": "Data Quality Test User"
    })
    login = client.post("/login", data={
        "username": username,
        "password": "testpassword"
    })
    assert login.status_code == 200
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Add sample data
    client.post("/glucose-readings", json={
        "value": 120,
        "unit": "mg/dl",
        "note": "Manual entry"
    }, headers=headers)
    
    client.post("/glucose-readings", json={
        "value": 140,
        "unit": "mg/dl",
        "note": "CSV upload"
    }, headers=headers)
    
    # Test data quality metrics
    response = client.get("/visualization/data-quality", headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert "data_quality" in data
    data_quality = data["data_quality"]
    assert "glucose_readings" in data_quality
    assert "meals" in data_quality
    assert "activities" in data_quality
    assert "insulin_doses" in data_quality
    assert "recommendations" in data
    assert "meta" in data

def test_unit_conversion_accuracy():
    """Test unit conversion accuracy."""
    from app.routers.visualization_router import convert_glucose_value
    
    # Test mg/dl to mmol/l conversion
    mgdl_value = 180
    mmol_value = convert_glucose_value(mgdl_value, "mg/dl", "mmol/l")
    expected_mmol = mgdl_value / 18
    assert abs(mmol_value - expected_mmol) < 0.01
    
    # Test mmol/l to mg/dl conversion
    mmol_value = 7.0
    mgdl_value = convert_glucose_value(mmol_value, "mmol/l", "mg/dl")
    expected_mgdl = mmol_value * 18
    assert abs(mgdl_value - expected_mgdl) < 0.01

def test_invalid_unit_parameter():
    """Test invalid unit parameter handling."""
    # Generate unique identifiers for this test run
    unique_id = str(uuid.uuid4())[:8]
    email = f"invalidunittest{unique_id}@example.com"
    username = f"invalidunittestuser{unique_id}"
    
    # Register and login user
    client.post("/users", json={
        "email": email,
        "username": username,
        "password": "testpassword",
        "name": "Invalid Unit Test User"
    })
    login = client.post("/login", data={
        "username": username,
        "password": "testpassword"
    })
    assert login.status_code == 200
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test with invalid unit
    response = client.get("/visualization/dashboard?unit=invalid", headers=headers)
    assert response.status_code == 400

def test_no_data_handling():
    """Test handling when no data is available."""
    # Generate unique identifiers for this test run
    unique_id = str(uuid.uuid4())[:8]
    email = f"nodatatest{unique_id}@example.com"
    username = f"nodatatestuser{unique_id}"
    
    # Register and login user
    client.post("/users", json={
        "email": email,
        "username": username,
        "password": "testpassword",
        "name": "No Data Test User"
    })
    login = client.post("/login", data={
        "username": username,
        "password": "testpassword"
    })
    assert login.status_code == 200
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test dashboard with no data
    response = client.get("/visualization/dashboard", headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert "dashboard" in data
    dashboard = data["dashboard"]
    assert "glucose_summary" in dashboard
    assert "recent_meals" in dashboard
    assert "upcoming_insulin" in dashboard
    assert "activity_summary" in dashboard
    assert "data_sources" in data

def test_custom_date_range():
    """Test custom date range functionality."""
    # Generate unique identifiers for this test run
    unique_id = str(uuid.uuid4())[:8]
    email = f"daterangetest{unique_id}@example.com"
    username = f"daterangetestuser{unique_id}"
    
    # Register and login user
    client.post("/users", json={
        "email": email,
        "username": username,
        "password": "testpassword",
        "name": "Date Range Test User"
    })
    login = client.post("/login", data={
        "username": username,
        "password": "testpassword"
    })
    assert login.status_code == 200
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Add sample data
    client.post("/glucose-readings", json={
        "value": 120,
        "unit": "mg/dl"
    }, headers=headers)
    
    # Test with custom date range
    response = client.get("/visualization/dashboard?start_date=2024-01-01&end_date=2024-12-31", headers=headers)
    assert response.status_code == 200

def test_missing_custom_date_parameters():
    """Test handling of missing custom date parameters."""
    # Generate unique identifiers for this test run
    unique_id = str(uuid.uuid4())[:8]
    email = f"missingdatetest{unique_id}@example.com"
    username = f"missingdatetestuser{unique_id}"
    
    # Register and login user
    client.post("/users", json={
        "email": email,
        "username": username,
        "password": "testpassword",
        "name": "Missing Date Test User"
    })
    login = client.post("/login", data={
        "username": username,
        "password": "testpassword"
    })
    assert login.status_code == 200
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test with only start_date
    response = client.get("/visualization/dashboard?start_date=2024-01-01", headers=headers)
    assert response.status_code == 200

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
        assert response.status_code in [401, 403]  # Both are valid for unauthenticated requests

def test_recommendations_integration():
    """Test integration with AI recommendations."""
    # Generate unique identifiers for this test run
    unique_id = str(uuid.uuid4())[:8]
    email = f"recommendationstest{unique_id}@example.com"
    username = f"recommendationstestuser{unique_id}"
    
    # Register and login user
    client.post("/users", json={
        "email": email,
        "username": username,
        "password": "testpassword",
        "name": "Recommendations Test User"
    })
    login = client.post("/login", data={
        "username": username,
        "password": "testpassword"
    })
    assert login.status_code == 200
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Add sample data
    client.post("/glucose-readings", json={
        "value": 120,
        "unit": "mg/dl"
    }, headers=headers)
    
    # Test dashboard includes recommendations
    response = client.get("/visualization/dashboard", headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert "dashboard" in data
    dashboard = data["dashboard"]
    assert "glucose_summary" in dashboard
    assert "recent_meals" in dashboard
    assert "upcoming_insulin" in dashboard
    assert "activity_summary" in dashboard
    assert "data_sources" in data 