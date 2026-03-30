from motor.motor_asyncio import AsyncIOMotorClient
from shared.core.config import MONGO_URL

mongo_client = AsyncIOMotorClient(MONGO_URL)
mongo_db = mongo_client.flight_data
