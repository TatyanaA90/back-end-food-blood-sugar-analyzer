from fastapi import FastAPI
from typing import Optional
from app.routers.user_router import router as user_router

app = FastAPI()

app.include_router(user_router)

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/items/{item_id}")
def read_item(item_id: int, q: Optional[str] = None):
    return {"item_id": item_id, "q": q}

@app.get("/ping")
def ping():
    return {"message": "pong"}