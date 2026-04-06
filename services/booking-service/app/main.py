from fastapi import FastAPI
from app.routers.bookings import bookings_router

from contextlib import asynccontextmanager

from app.services.kafka_producer import start_kafka_producer, stop_kafka_producer


@asynccontextmanager
async def lifespan(app: FastAPI):
    await start_kafka_producer()
    yield
    await stop_kafka_producer()

app = FastAPI(title="Booking Service", lifespan=lifespan)

@app.get("/")
async def root():
    return {"message": "Booking Service Running"}

app.include_router(bookings_router)
