from fastapi import APIRouter, FastAPI

api_router = APIRouter(prefix="/api/v1")

def register_routers(app: FastAPI):
    app.include_router(api_router)
