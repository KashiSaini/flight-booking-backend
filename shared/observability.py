from datetime import datetime
from typing import Optional

from shared.db.mongo import mongo_db

async def log_user_activity(user_id: int, action: str, details: dict | None = None):
    log_entry = {
        "user_id": user_id,
        "action": action,
        "details": details or {},
        "timestamp": datetime.utcnow(),
    }
    await mongo_db.user_activity.insert_one(log_entry)

async def increment_flight_analytics(flight_id: int, metric_name: str):
    await mongo_db.flight_analytics.update_one(
        {"flight_id": flight_id},
        {"$inc": {metric_name: 1}},
        upsert=True,
    )

async def get_user_activity_logs(limit: int = 50, skip: int = 0):
    cursor = mongo_db.user_activity.find().sort("timestamp", -1).skip(skip).limit(limit)
    logs = await cursor.to_list(length=limit)
    for log in logs:
        log["_id"] = str(log["_id"])
    return logs

async def get_all_flight_analytics(flight_id: Optional[int] = None):
    query = {}
    if flight_id:
        query["flight_id"] = flight_id
    cursor = mongo_db.flight_analytics.find(query)
    analytics_data = await cursor.to_list(length=1000)
    for data in analytics_data:
        data["_id"] = str(data["_id"])
    return analytics_data
