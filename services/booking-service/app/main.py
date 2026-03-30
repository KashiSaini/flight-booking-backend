from fastapi import FastAPI
from app.routers.bookings import bookings_router

app = FastAPI(title="Booking Service")

@app.get("/")
async def root():
    return {"message": "Booking Service Running"}

app.include_router(bookings_router)
