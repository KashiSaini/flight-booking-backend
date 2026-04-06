from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.routers.admin import admin_router
from app.services.kafka_consumer import start_kafka_consumer, stop_kafka_consumer


@asynccontextmanager
async def lifespan(app: FastAPI):
    await start_kafka_consumer()
    yield
    await stop_kafka_consumer()


app = FastAPI(title="Admin Service", lifespan=lifespan)


@app.get("/")
async def root():
    return {"message": "Admin Service Running"}


app.include_router(admin_router)