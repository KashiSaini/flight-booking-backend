import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv()

MONGO_URL = os.getenv("MONGO_URL")

# Create the async connection to MongoDB
mongo_client = AsyncIOMotorClient(MONGO_URL)

# Select the specific database you want to use (let's call it 'flight_data')
mongo_db = mongo_client.flight_data
