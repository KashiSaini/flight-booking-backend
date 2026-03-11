from contextlib import asynccontextmanager
from fastapi import FastAPI
from app import auth, booking, admin

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

app = FastAPI(lifespan=lifespan,
              )

@app.get("/")
async def root():
    return {"message": "Flight Booking API is running"}

app.include_router(auth.router)
app.include_router(booking.router)
app.include_router(booking.bookings_router)
app.include_router(booking.privatejet_router)
app.include_router(admin.admin_router)