from fastapi import FastAPI
from app.routers.auth import router as auth_router

app = FastAPI(title="Auth Service")

@app.get("/")
async def root():
    return {"message": "Auth Service Running"}

app.include_router(auth_router)
