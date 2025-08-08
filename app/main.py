from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from datetime import datetime, UTC
from fastapi.responses import HTMLResponse
from app.routers.user_router import router as user_router
from app.routers.admin_router import router as admin_router
from app.routers.meal_plan_router import router as meal_router
from app.routers.predefined_meal_router import router as predefined_meal_router
from app.routers.activity_router import router as activity_router
from app.routers.insulin_dose_router import router as insulin_dose_router
from app.routers.glucose_reading_router import router as glucose_reading_router
from app.routers.logs_router import router as logs_router
from app.routers.dexcom_upload_router import router as dexcom_upload_router
from app.routers.analytics_router import router as analytics_router
from app.routers.visualization_router import router as visualization_router
from app.documentation_template import DOCUMENTATION_HTML

app = FastAPI(
    title="Food & Blood Sugar Analyzer API",
    description="A comprehensive API for diabetes management and blood sugar analysis. [View Full Documentation](/documentation)",
    version="1.0.0",
    contact={
        "name": "Food & Blood Sugar Analyzer Team",
        "email": "support@foodbloodsugar.com",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
    servers=[
        {
            "url": "http://localhost:8000",
            "description": "Development server"
        },
        {
            "url": "https://api.foodbloodsugar.com",
            "description": "Production server"
        }
    ],
    tags_metadata=[
        {
            "name": "authentication",
            "description": "User registration, login, and authentication operations."
        },
        {
            "name": "meals",
            "description": "Meal tracking with ingredients, nutritional data, and carb calculations."
        },
        {
            "name": "activities",
            "description": "Exercise and activity tracking with MET-based calorie calculations."
        },
        {
            "name": "glucose-readings",
            "description": "Blood sugar monitoring with unit conversion support (mg/dl ↔ mmol/l)."
        },
        {
            "name": "insulin-doses",
            "description": "Insulin injection tracking with meal relationships and dose optimization."
        },
        {
            "name": "condition-logs",
            "description": "Health condition and symptom tracking for comprehensive monitoring."
        },
        {
            "name": "cgm-upload",
            "description": "CSV upload functionality for continuous glucose monitoring data."
        },
        {
            "name": "analytics",
            "description": "Advanced analytics and insights for diabetes management and pattern recognition."
        },
        {
            "name": "visualization",
            "description": "Clean data endpoints for frontend visualization and dashboard creation."
        },
        {
            "name": "admin",
            "description": "Administrative operations for user management and system administration."
        }
    ]
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://food-blood-sugar-analyzer-frontend.onrender.com",  # Production frontend
        "http://localhost:5173",  # Vite dev server
        "http://localhost:3000",  # Alternative dev server
        "http://127.0.0.1:5173",  # Alternative local
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],  # Explicitly list all methods
    allow_headers=["*"],
    expose_headers=["*"]
)

app.include_router(user_router)
app.include_router(admin_router)
app.include_router(predefined_meal_router)
app.include_router(meal_router)
app.include_router(activity_router)
app.include_router(insulin_dose_router)
app.include_router(glucose_reading_router)
app.include_router(logs_router)
app.include_router(dexcom_upload_router)
app.include_router(analytics_router)
app.include_router(visualization_router)


@app.get("/", tags=["root"])
def read_root():
    """
    Root endpoint providing API information and quick links.
    """
    return {
        "message": "Food & Blood Sugar Analyzer API",
        "version": "1.0.0",
        "description": "A comprehensive API for diabetes management and blood sugar analysis",
        "documentation": {
            "swagger_ui": "/docs",
            "redoc": "/redoc",
            "openapi_json": "/openapi.json",
            "full_documentation": "/documentation"
        },
        "endpoints": {
            "authentication": "/users, /login, /me",
            "data_management": "/meals, /activities, /glucose-readings, /insulin-doses, /condition-logs",
            "analytics": "/analytics/*",
            "visualization": "/visualization/*",
            "data_import": "/cgm-upload"
        },
        "features": [
            "User authentication with JWT",
            "Glucose monitoring with unit conversion",
            "Meal tracking with nutritional analysis",
            "Activity tracking with calorie calculations",
            "Insulin dose management",
            "Advanced analytics and AI insights",
            "Visualization data endpoints",
            "CSV data import"
        ]
    }

@app.get("/documentation", response_class=HTMLResponse, tags=["documentation"])
def get_documentation_page():
    """
    Comprehensive API documentation page with full project description.
    """
    return HTMLResponse(content=DOCUMENTATION_HTML)

@app.get("/health", tags=["health"])
def health_check():
    """
    Health check endpoint for monitoring API status.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now(UTC).isoformat(),
        "version": "1.0.0"
    }

@app.get("/ping", tags=["health"])
def ping():
    """
    Simple ping endpoint for connectivity testing.
    """
    return {"message": "pong", "timestamp": datetime.now(UTC).isoformat()}