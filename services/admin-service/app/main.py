from fastapi import FastAPI
from app.routers.admin import admin_router

app = FastAPI(title="Admin Service")

@app.get("/")
async def root():
    return {"message": "Admin Service Running"}

app.include_router(admin_router)
