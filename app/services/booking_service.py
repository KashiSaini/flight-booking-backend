from fastapi import HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import uuid

from app.db.redis import redis_client
from app.services.admin_service import log_user_activity
from app.models.user import User
from app.models.flight import Flight, Seat
from app.models.booking import  Booking
from app.schemas.booking import BookingCreate


def _compute_price_for_destination(flight: Flight, seat_type: str, destination: str) -> float:
    route = [flight.source] + (flight.stops or []) + [flight.destination]

    try:
        dest_index = route.index(destination)
    except ValueError:
        return getattr(flight, f"{seat_type}_price") or 0.0

    segs = flight.segment_prices if getattr(flight, "segment_prices", None) else None
    if not segs or len(segs) != len(route) - 1:
        return getattr(flight, f"{seat_type}_price") or 0.0

    total = 0.0
    for i in range(dest_index):
        seg = segs[i]
        price = seg.get(seat_type)
        if price is None:
            return getattr(flight, f"{seat_type}_price") or 0.0
        total += float(price)

    return total


async def book_flight(
    flight_id: int,
    booking_in: BookingCreate,
    background_tasks: BackgroundTasks,
    current_user: User,
    db: AsyncSession,
):
    if not booking_in.passengers:
        raise HTTPException(status_code=400, detail="At least one passenger is required")

    result = await db.execute(
        select(Flight).where(Flight.id == flight_id).with_for_update()
    )
    flight = result.scalar_one_or_none()

    if not flight:
        raise HTTPException(status_code=404, detail="Flight not found")

    allowed_destinations = []
    if flight.stops:
        allowed_destinations.extend(flight.stops)
    allowed_destinations.append(flight.destination)

    bookings = []
    for passenger in booking_in.passengers:
        if not passenger.destination:
            raise HTTPException(status_code=400, detail="Each passenger must include a destination on this flight route")

        if passenger.destination not in allowed_destinations:
            raise HTTPException(
                status_code=400,
                detail=f"Destination '{passenger.destination}' is not on this flight route"
            )

        if not passenger.seat_number:
            raise HTTPException(status_code=400, detail="Each passenger must select a seat_number")

        seat_res = await db.execute(
            select(Seat)
            .where(Seat.flight_id == flight_id, Seat.seat_number == passenger.seat_number)
            .with_for_update()
        )
        seat = seat_res.scalar_one_or_none()

        if not seat:
            raise HTTPException(status_code=400, detail=f"Seat {passenger.seat_number} does not exist on this flight")

        if seat.is_booked:
            raise HTTPException(status_code=400, detail=f"Seat {passenger.seat_number} is already booked")

        if seat.seat_type != passenger.seat_type:
            raise HTTPException(
                status_code=400,
                detail=f"Seat {passenger.seat_number} is a {seat.seat_type} seat, not {passenger.seat_type}"
            )

        seat.is_booked = True

        price_paid = _compute_price_for_destination(flight, passenger.seat_type, passenger.destination)

        booking = Booking(
            user_id=current_user.id,
            flight_id=flight_id,
            seat_id=seat.id,
            seat_number=seat.seat_number,
            seat_type=passenger.seat_type,
            price_paid=price_paid,
            passenger_name=passenger.passenger_name,
            destination=passenger.destination,
            booking_reference=str(uuid.uuid4())[:8].upper(),
        )
        db.add(booking)
        bookings.append(booking)

        if passenger.seat_type == "business":
            flight.business_seats = (flight.business_seats or 0) - 1
        elif passenger.seat_type == "premium":
            flight.premium_seats = (flight.premium_seats or 0) - 1
        elif passenger.seat_type == "economy":
            flight.economy_seats = (flight.economy_seats or 0) - 1

    await db.commit()

    for booking in bookings:
        await db.refresh(booking)

    await redis_client.delete("flights_cache")

    background_tasks.add_task(
        log_user_activity,
        user_id=current_user.id,
        action="BOOKED_FLIGHT",
        details={
            "flight_id": flight_id,
            "number_of_passengers": len(booking_in.passengers),
            "booking_references": [b.booking_reference for b in bookings],
            "Booked_By": current_user.name
        }
    )

    return bookings


async def get_user_bookings(
    skip: int,
    limit: int,
    current_user: User,
    db: AsyncSession,
):
    result = await db.execute(
        select(Booking)
        .where(Booking.user_id == current_user.id)
        .offset(skip)
        .limit(limit)
    )
    bookings = result.scalars().all()
    return bookings


async def get_booking(
    booking_id: int,
    current_user: User,
    db: AsyncSession,
):
    result = await db.execute(
        select(Booking).where((Booking.id == booking_id) & (Booking.user_id == current_user.id))
    )
    booking = result.scalar_one_or_none()

    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    return booking


async def cancel_booking(
    booking_id: int,
    background_tasks: BackgroundTasks,
    current_user: User,
    db: AsyncSession,
):
    result = await db.execute(
        select(Booking).where((Booking.id == booking_id) & (Booking.user_id == current_user.id))
    )
    booking = result.scalar_one_or_none()

    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")

    flight_result = await db.execute(
        select(Flight).where(Flight.id == booking.flight_id).with_for_update()
    )
    flight = flight_result.scalar_one_or_none()

    if not flight:
        raise HTTPException(status_code=404, detail="Flight not found")

    if booking.seat_id:
        seat_res = await db.execute(
            select(Seat).where(Seat.id == booking.seat_id).with_for_update()
        )
        seat = seat_res.scalar_one_or_none()
        if seat:
            seat.is_booked = False
    elif booking.seat_number:
        seat_res = await db.execute(
            select(Seat)
            .where(Seat.flight_id == booking.flight_id, Seat.seat_number == booking.seat_number)
            .with_for_update()
        )
        seat = seat_res.scalar_one_or_none()
        if seat:
            seat.is_booked = False

    if booking.seat_type == "business":
        flight.business_seats = (flight.business_seats or 0) + 1
    elif booking.seat_type == "premium":
        flight.premium_seats = (flight.premium_seats or 0) + 1
    elif booking.seat_type == "economy":
        flight.economy_seats = (flight.economy_seats or 0) + 1

    await db.delete(booking)
    await db.commit()
    await redis_client.delete("flights_cache")

    background_tasks.add_task(
        log_user_activity,
        user_id=current_user.id,
        action="CANCEL_BOOKING",
        details={
            "booking_id": booking_id,
            "BY": current_user.name
        }
    )

    return {"message": "Booking cancelled successfully"}