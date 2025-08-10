import pytest
import uuid

def test_create_condition_log(client, test_user, auth_headers):
    # Create condition log
    response = client.post("/condition-logs", json={
        "type": "Stress",
        "value": "High"
    }, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["type"] == "Stress"
    assert data["value"] == "High"