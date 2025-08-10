import pytest
import uuid
from datetime import datetime, timedelta, UTC
from sqlalchemy import select

def test_glucose_summary_whole_range(client, test_user, auth_headers):
    # Add a glucose reading
    client.post("/glucose-readings", json={
        "value": 110,
        "unit": "mg/dl"
    }, headers=auth_headers)
    # Test whole-range summary
    response = client.get("/analytics/glucose-summary", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "average" in data
    assert "min" in data
    assert "max" in data
    assert "std_dev" in data
    assert "num_readings" in data
    assert "in_target_percent" in data

def test_glucose_summary_by_day(client, test_user, auth_headers):
    # Add a glucose reading
    client.post("/glucose-readings", json={
        "value": 120,
        "unit": "mg/dl"
    }, headers=auth_headers)
    # Test group_by=day
    response = client.get("/analytics/glucose-summary?group_by=day", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "summary" in data
    assert "meta" in data