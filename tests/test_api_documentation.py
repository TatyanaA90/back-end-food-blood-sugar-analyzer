import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_root_endpoint():
    """Test the root endpoint provides comprehensive API information."""
    response = client.get("/")
    assert response.status_code == 200
    
    data = response.json()
    assert data["message"] == "Food & Blood Sugar Analyzer API"
    assert data["version"] == "1.0.0"
    assert "documentation" in data
    assert "endpoints" in data
    assert "features" in data
    
    # Check documentation links
    docs = data["documentation"]
    assert docs["swagger_ui"] == "/docs"
    assert docs["redoc"] == "/redoc"
    assert docs["openapi_json"] == "/openapi.json"

def test_health_endpoint():
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "healthy"
    assert data["version"] == "1.0.0"
    assert "timestamp" in data

def test_ping_endpoint():
    """Test the ping endpoint."""
    response = client.get("/ping")
    assert response.status_code == 200
    
    data = response.json()
    assert data["message"] == "pong"
    assert "timestamp" in data

def test_openapi_json():
    """Test that OpenAPI JSON is accessible and properly formatted."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    
    data = response.json()
    assert data["info"]["title"] == "Food & Blood Sugar Analyzer API"
    assert data["info"]["version"] == "1.0.0"
    assert "paths" in data
    assert "servers" in data

def test_swagger_ui_accessible():
    """Test that Swagger UI is accessible."""
    response = client.get("/docs")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]

def test_redoc_accessible():
    """Test that ReDoc is accessible."""
    response = client.get("/redoc")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]

def test_api_info_metadata():
    """Test that API metadata is properly set."""
    response = client.get("/openapi.json")
    data = response.json()
    
    info = data["info"]
    assert info["title"] == "Food & Blood Sugar Analyzer API"
    assert info["version"] == "1.0.0"
    assert "description" in info
    assert "contact" in info
    assert "license" in info
    
    # Check contact information
    contact = info["contact"]
    assert contact["name"] == "Food & Blood Sugar Analyzer Team"
    assert contact["email"] == "support@foodbloodsugar.com"
    
    # Check license information
    license_info = info["license"]
    assert license_info["name"] == "MIT"
    assert license_info["url"] == "https://opensource.org/licenses/MIT"

def test_servers_configuration():
    """Test that servers are properly configured."""
    response = client.get("/openapi.json")
    data = response.json()
    
    servers = data["servers"]
    assert len(servers) == 2
    
    # Check development server
    dev_server = servers[0]
    assert dev_server["url"] == "http://localhost:8000"
    assert dev_server["description"] == "Development server"
    
    # Check production server
    prod_server = servers[1]
    assert prod_server["url"] == "https://api.foodbloodsugar.com"
    assert prod_server["description"] == "Production server"

def test_endpoint_coverage():
    """Test that all major endpoint categories are documented."""
    response = client.get("/")
    data = response.json()
    
    endpoints = data["endpoints"]
    assert "authentication" in endpoints
    assert "data_management" in endpoints
    assert "analytics" in endpoints
    assert "visualization" in endpoints
    assert "data_import" in endpoints

def test_feature_list():
    """Test that all major features are listed."""
    response = client.get("/")
    data = response.json()
    
    features = data["features"]
    expected_features = [
        "User authentication with JWT",
        "Glucose monitoring with unit conversion",
        "Meal tracking with nutritional analysis",
        "Activity tracking with calorie calculations",
        "Insulin dose management",
        "Advanced analytics and AI insights",
        "Visualization data endpoints",
        "CSV data import"
    ]
    
    for feature in expected_features:
        assert feature in features 