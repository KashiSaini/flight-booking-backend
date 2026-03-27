from typing import List, Optional
from fastapi import APIRouter, Depends
from app.mongodb import mongo_db
from app.dependencies import get_admin_user
from app.models import User


admin_router = APIRouter(prefix="/admin", tags=["Admin"])

@admin_router.get("/logs")
async def get_user_activity_logs(
    limit: int = 50, 
    skip: int = 0,
    current_user: User = Depends(get_admin_user) # Admins only!
):
    

    cursor = mongo_db.user_activity.find().sort("timestamp", -1).skip(skip).limit(limit)
    
    # Convert the async cursor into a standard Python list
    logs = await cursor.to_list(length=limit)
    
    # Convert MongoDB's special ObjectId into a normal string
    for log in logs:
        log["_id"] = str(log["_id"])
        
    return logs


@admin_router.get("/analytics")
async def get_all_flight_analytics(
    flight_id: Optional[int] = None, # Optional filter if the admin only wants one flight
    current_user: User = Depends(get_admin_user) # SECURITY: Admins only!
):

    
    query = {}
    if flight_id:
        query["flight_id"] = flight_id
        
    # Ask Mongo for the data
    cursor = mongo_db.flight_analytics.find(query)
    
    # Convert to a list (1000 records at a time)
    analytics_data = await cursor.to_list(length=1000)
    
    # Convert the _id
    for data in analytics_data:
        data["_id"] = str(data["_id"])
        
    return analytics_data