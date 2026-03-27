from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.db.postgres import get_db
from app.models.user import User
from app.schemas.booking import BookingResponse
from app.api.dependencies.auth import get_current_logged_user
from app.services import booking_service

bookings_router = APIRouter(prefix="/bookings", tags=["Bookings"])


@bookings_router.get("/", response_model=List[BookingResponse])
async def get_user_bookings(
    skip: int = 0,
    limit: int = 10,
    current_user: User = Depends(get_current_logged_user),
    db: AsyncSession = Depends(get_db),
):
    return await booking_service.get_user_bookings(
        skip=skip,
        limit=limit,
        current_user=current_user,
        db=db,
    )


@bookings_router.get("/{booking_id}", response_model=BookingResponse)
async def get_booking(
    booking_id: int,
    current_user: User = Depends(get_current_logged_user),
    db: AsyncSession = Depends(get_db),
):
    return await booking_service.get_booking(
        booking_id=booking_id,
        current_user=current_user,
        db=db,
    )


@bookings_router.delete("/{booking_id}")
async def cancel_booking(
    booking_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_logged_user),
    db: AsyncSession = Depends(get_db),
):
    return await booking_service.cancel_booking(
        booking_id=booking_id,
        background_tasks=background_tasks,
        current_user=current_user,
        db=db,
    )