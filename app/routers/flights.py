from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Literal

from app.db.postgres import get_db
from app.models.user import User
from app.schemas.flight import FlightCreate, FlightResponse, SeatResponse
from app.schemas.booking import BookingCreate, BookingResponse
from app.api.dependencies.auth import get_current_logged_user, get_admin_user
from app.services import flight_service, booking_service

router = APIRouter(prefix="/flights", tags=["Flights"])


@router.get("/", response_model=List[FlightResponse])
async def get_all_flights(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_logged_user),
    skip: int = 0,
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
):
    return await flight_service.get_all_flights(
        background_tasks=background_tasks,
        current_user=current_user,
        skip=skip,
        limit=limit,
        db=db,
    )


@router.post("/", response_model=FlightResponse)
async def create_flight(
    flight: FlightCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    return await flight_service.create_flight(
        flight=flight,
        background_tasks=background_tasks,
        db=db,
        current_user=current_user,
    )


@router.get("/{flight_id}/seats", response_model=List[SeatResponse])
async def get_flight_seats(
    flight_id: int,
    available: bool = True,
    db: AsyncSession = Depends(get_db),
):
    return await flight_service.get_flight_seats(
        flight_id=flight_id,
        available=available,
        db=db,
    )


@router.post("/{flight_id}/book", response_model=List[BookingResponse])
async def book_flight(
    flight_id: int,
    booking_in: BookingCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_logged_user),
    db: AsyncSession = Depends(get_db),
):
    return await booking_service.book_flight(
        flight_id=flight_id,
        booking_in=booking_in,
        background_tasks=background_tasks,
        current_user=current_user,
        db=db,
    )


@router.get("/search", response_model=List[FlightResponse])
async def search_flights(
    background_tasks: BackgroundTasks,
    source: Optional[str] = None,
    destination: Optional[str] = None,
    departure_date: Optional[str] = None,
    price_max: Optional[float] = None,
    seat_class: Optional[Literal["business", "premium", "economy"]] = None,
    db: AsyncSession = Depends(get_db),
):
    return await flight_service.search_flights(
        background_tasks=background_tasks,
        source=source,
        destination=destination,
        departure_date=departure_date,
        price_max=price_max,
        seat_class=seat_class,
        db=db,
    )


@router.put("/{flight_id}", response_model=FlightResponse)
async def update_flight(
    flight_id: int,
    flight_in: FlightCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    return await flight_service.update_flight(
        flight_id=flight_id,
        flight_in=flight_in,
        background_tasks=background_tasks,
        current_user=current_user,
        db=db,
    )


@router.delete("/{flight_id}")
async def delete_flight(
    flight_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    return await flight_service.delete_flight(
        flight_id=flight_id,
        background_tasks=background_tasks,
        current_user=current_user,
        db=db,
    )