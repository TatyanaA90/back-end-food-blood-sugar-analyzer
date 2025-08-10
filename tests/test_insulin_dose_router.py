import pytest
import uuid

def test_create_insulin_dose(client, test_user, auth_headers):
    # Create insulin dose
    response = client.post("/insulin-doses", json={
        "units": 5.0
    }, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["units"] == 5.0