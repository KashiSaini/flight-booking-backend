from fastapi import FastAPI
from app.routers.flights import router as flights_router

app = FastAPI(title="Flight Service")

@app.get("/")
async def root():
    return {"message": "Flight Service Running"}

app.include_router(flights_router)
