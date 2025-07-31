from fastapi import FastAPI
from typing import Optional
from app.routers.user_router import router as user_router
from app.routers.meal_plan_router import router as meal_router
from app.routers.activity_router import router as activity_router
from app.routers.insulin_dose_router import router as insulin_dose_router
from app.routers.glucose_reading_router import router as glucose_reading_router
from app.routers.logs_router import router as logs_router
from app.routers.dexcom_upload_router import router as dexcom_upload_router
from app.routers.analytics_router import router as analytics_router
from app.routers.visualization_router import router as visualization_router

app = FastAPI()

app.include_router(user_router)
app.include_router(meal_router)
app.include_router(activity_router)
app.include_router(insulin_dose_router)
app.include_router(glucose_reading_router)
app.include_router(logs_router)
app.include_router(dexcom_upload_router)
app.include_router(analytics_router)
app.include_router(visualization_router)

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/items/{item_id}")
def read_item(item_id: int, q: Optional[str] = None):
    return {"item_id": item_id, "q": q}

@app.get("/ping")
def ping():
    return {"message": "pong"}