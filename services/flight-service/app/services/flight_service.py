import json
from datetime import datetime, timezone
from typing import Literal, Optional

from fastapi import BackgroundTasks, HTTPException
from sqlalchemy import String, and_, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.flight import FlightCreate, FlightResponse
from shared.db.redis import redis_client
from shared.models.flight import Flight, Seat
from shared.models.user import User
from shared.observability import increment_flight_analytics, log_user_activity

async def get_all_flights(
    background_tasks: BackgroundTasks,
    current_user: User,
    skip: int,
    limit: int,
    db: AsyncSession,
):
    cached_flights = await redis_client.get("flights_cache")
    if cached_flights:
        flights_data = json.loads(cached_flights)
        return flights_data[skip : skip + limit]

    result = await db.execute(select(Flight))
    flights = result.scalars().all()
    flights_data = [FlightResponse.model_validate(f).model_dump() for f in flights]

    for fd in flights_data:
        for dt_key in ("departure_time", "arrival_time"):
            if fd.get(dt_key) is not None and isinstance(fd[dt_key], datetime):
                fd[dt_key] = fd[dt_key].isoformat()

    if flights_data:
        await redis_client.setex("flights_cache", 60, json.dumps(flights_data))

    paginated = flights_data[skip : skip + limit]

    background_tasks.add_task(
        log_user_activity,
        user_id=current_user.id,
        action="SEARCH_ALL_FLIGHT",
        details={"number_of_flights_returned": len(paginated), "BY": current_user.name},
    )
    return paginated

async def create_flight(
    flight: FlightCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession,
    current_user: User,
):
    data = flight.model_dump()

    for key in ("departure_time", "arrival_time"):
        if data.get(key):
            dt = data[key]
            if isinstance(dt, datetime) and dt.tzinfo is not None:
                data[key] = dt.astimezone(timezone.utc).replace(tzinfo=None)

    stops = data.get("stops") or []
    seg_prices = data.get("segment_prices")
    if stops:
        expected = len(stops) + 1
        if not seg_prices or len(seg_prices) != expected:
            raise HTTPException(
                status_code=400,
                detail=f"segment_prices must be provided with {expected} entries when stops are set",
            )
        for sp in seg_prices:
            if not all(k in sp for k in ("from_location", "to_location", "business", "premium", "economy")):
                raise HTTPException(
                    status_code=400,
                    detail="each segment_prices item must include from_location, to_location, business, premium, economy keys",
                )

    max_seats_per_class = 500
    if data.get("business_seats", 0) > max_seats_per_class:
        raise HTTPException(status_code=400, detail=f"Maximum {max_seats_per_class} business seats allowed")
    if data.get("premium_seats", 0) > max_seats_per_class:
        raise HTTPException(status_code=400, detail=f"Maximum {max_seats_per_class} premium seats allowed")
    if data.get("economy_seats", 0) > max_seats_per_class:
        raise HTTPException(status_code=400, detail=f"Maximum {max_seats_per_class} economy seats allowed")

    new_flight = Flight(**data)
    db.add(new_flight)
    await db.commit()
    await db.refresh(new_flight)

    seats_to_add = []
    for i in range(new_flight.business_seats or 0):
        seats_to_add.append(Seat(flight_id=new_flight.id, seat_number=f"B{i+1}", seat_type="business", is_booked=False))
    for i in range(new_flight.premium_seats or 0):
        seats_to_add.append(Seat(flight_id=new_flight.id, seat_number=f"P{i+1}", seat_type="premium", is_booked=False))
    for i in range(new_flight.economy_seats or 0):
        seats_to_add.append(Seat(flight_id=new_flight.id, seat_number=f"E{i+1}", seat_type="economy", is_booked=False))

    if seats_to_add:
        db.add_all(seats_to_add)
        await db.commit()

    await redis_client.delete("flights_cache")

    background_tasks.add_task(
        log_user_activity,
        user_id=current_user.id,
        action="CREATE_FLIGHT",
        details={"flight_id": new_flight.id, "source": new_flight.source, "destination": new_flight.destination, "BY": current_user.name},
    )

    return new_flight

async def get_flight_seats(flight_id: int, available: bool, db: AsyncSession):
    query = select(Seat).where(Seat.flight_id == flight_id)
    if available:
        query = query.where(Seat.is_booked == False)
    result = await db.execute(query)
    return result.scalars().all()

async def search_flights(
    background_tasks: BackgroundTasks,
    source: Optional[str],
    destination: Optional[str],
    departure_date: Optional[str],
    price_max: Optional[float],
    seat_class: Optional[Literal["business", "premium", "economy"]],
    db: AsyncSession,
):
    filters = []

    if source:
        filters.append((Flight.source == source) | (cast(Flight.stops, String).ilike(f"%{source}%")))
    if destination:
        filters.append((Flight.destination == destination) | (cast(Flight.stops, String).ilike(f"%{destination}%")))
    if departure_date:
        try:
            dt = datetime.fromisoformat(departure_date).date()
            filters.append(func.date(Flight.departure_time) == dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="departure_date must be YYYY-MM-DD")
    if price_max is not None and seat_class in ("business", "premium", "economy"):
        col = getattr(Flight, f"{seat_class}_price")
        filters.append(col <= price_max)

    query = select(Flight).where(and_(*filters)) if filters else select(Flight)
    result = await db.execute(query)
    flights = result.scalars().all()

    for flight in flights:
        background_tasks.add_task(increment_flight_analytics, flight_id=flight.id, metric_name="search_count")

    return [FlightResponse.model_validate(f).model_dump() for f in flights]

async def update_flight(
    flight_id: int,
    flight_in: FlightCreate,
    background_tasks: BackgroundTasks,
    current_user: User,
    db: AsyncSession,
):
    result = await db.execute(select(Flight).where(Flight.id == flight_id).with_for_update())
    flight = result.scalar_one_or_none()
    if not flight:
        raise HTTPException(status_code=404, detail="Flight not found")

    for key, value in flight_in.model_dump().items():
        if value and key in ("departure_time", "arrival_time") and isinstance(value, datetime) and value.tzinfo is not None:
            value = value.astimezone(timezone.utc).replace(tzinfo=None)
        setattr(flight, key, value)

    await db.commit()
    await db.refresh(flight)

    existing = await db.execute(select(Seat).where(Seat.flight_id == flight.id))
    existing_seats = existing.scalars().all()
    counts = {"business": 0, "premium": 0, "economy": 0}
    for seat in existing_seats:
        counts[seat.seat_type] += 1

    seats_to_add = []
    if flight.business_seats and flight.business_seats > counts["business"]:
        for i in range(counts["business"], flight.business_seats):
            seats_to_add.append(Seat(flight_id=flight.id, seat_number=f"B{i+1}", seat_type="business"))
    if flight.premium_seats and flight.premium_seats > counts["premium"]:
        for i in range(counts["premium"], flight.premium_seats):
            seats_to_add.append(Seat(flight_id=flight.id, seat_number=f"P{i+1}", seat_type="premium"))
    if flight.economy_seats and flight.economy_seats > counts["economy"]:
        for i in range(counts["economy"], flight.economy_seats):
            seats_to_add.append(Seat(flight_id=flight.id, seat_number=f"E{i+1}", seat_type="economy"))

    if seats_to_add:
        db.add_all(seats_to_add)
        await db.commit()

    await redis_client.delete("flights_cache")
    background_tasks.add_task(
        log_user_activity,
        user_id=current_user.id,
        action="UPDATE_FLIGHT",
        details={"flight_id": flight_id, "updated_fields": list(flight_in.model_dump().keys()), "BY": current_user.name},
    )
    return flight

async def delete_flight(
    flight_id: int,
    background_tasks: BackgroundTasks,
    current_user: User,
    db: AsyncSession,
):
    result = await db.execute(select(Flight).where(Flight.id == flight_id))
    flight = result.scalar_one_or_none()
    if not flight:
        raise HTTPException(status_code=404, detail="Flight not found")

    background_tasks.add_task(
        log_user_activity,
        user_id=current_user.id,
        action="DELETE_FLIGHT",
        details={"flight_id": flight_id, "BY": current_user.name},
    )

    await db.delete(flight)
    await db.commit()
    await redis_client.delete("flights_cache")
    return {"message": "Flight deleted"}
