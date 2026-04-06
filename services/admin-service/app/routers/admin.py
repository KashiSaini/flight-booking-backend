from typing import Optional

from fastapi import APIRouter, Depends

from app.services import admin_service
from shared.dependencies.auth import get_admin_user
from shared.models.user import User

admin_router = APIRouter(prefix="/admin", tags=["Admin"])


@admin_router.get("/logs")
async def get_user_activity_logs(
    limit: int = 50,
    skip: int = 0,
    current_user: User = Depends(get_admin_user),
):
    return await admin_service.get_user_activity_logs(limit=limit, skip=skip)


@admin_router.get("/analytics")
async def get_all_flight_analytics(
    flight_id: Optional[int] = None,
    current_user: User = Depends(get_admin_user),
):
    return await admin_service.get_all_flight_analytics(flight_id=flight_id)


@admin_router.get("/booking-events")
async def get_booking_events(
    limit: int = 50,
    skip: int = 0,
    event_type: Optional[str] = None,
    current_user: User = Depends(get_admin_user),
):
    return await admin_service.get_booking_events(
        limit=limit,
        skip=skip,
        event_type=event_type,
    )