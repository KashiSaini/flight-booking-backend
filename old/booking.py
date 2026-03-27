
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, cast, String
import json
from typing import List, Optional, Literal
from datetime import datetime, timezone
from app.utils import log_user_activity, increment_flight_analytics
from fastapi import BackgroundTasks
import uuid
from app.redis_client import redis_client
from app.database import get_db
from app.models import Flight, Booking, User, Seat, PrivateJet, PrivateJetBooking
from app.schemas import (
    FlightCreate,
    FlightResponse,
    BookingResponse,
    BookingCreate,
    SeatResponse,
    PrivateJetCreate,
    PrivateJetResponse,
    PrivateJetBookingCreate,
    PrivateJetBookingResponse,
)
from app.dependencies import get_current_logged_user, get_admin_user



router = APIRouter(prefix="/flights", tags=["Flights"])
bookings_router = APIRouter(prefix="/bookings", tags=["Bookings"])
privatejet_router = APIRouter(prefix="/private-jets", tags=["Private Jets"])

# --- Private jets endpoints ---
@privatejet_router.post("/", response_model=PrivateJetResponse)
async def create_private_jet(
    jet_in: PrivateJetCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    data = jet_in.model_dump()
    # normalize aware datetimes to UTC naive for DB (TIMESTAMP without TZ)
    for k in ("available_from", "available_to"):
        if data.get(k):
            dt = data[k]
            if isinstance(dt, datetime) and dt.tzinfo is not None:
                data[k] = dt.astimezone(timezone.utc).replace(tzinfo=None)
    pj = PrivateJet(**data, owner_id=current_user.id)
    db.add(pj)
    await db.commit()
    await db.refresh(pj)
    return pj


@privatejet_router.get("/", response_model=List[PrivateJetResponse])
async def list_private_jets(available: Optional[bool] = True, db: AsyncSession = Depends(get_db)):
    q = select(PrivateJet)
    if available:
        q = q.where(PrivateJet.is_available == True)
    res = await db.execute(q)
    return res.scalars().all()


@privatejet_router.post("/{jet_id}/book", response_model=PrivateJetBookingResponse)
async def book_private_jet(
    jet_id: int,
    booking_in: PrivateJetBookingCreate,
    current_user: User = Depends(get_current_logged_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(PrivateJet).where(PrivateJet.id == jet_id).with_for_update())
    pj = result.scalar_one_or_none()
    if not pj:
        raise HTTPException(status_code=404, detail="Private jet not found")
    if not pj.is_available:
        raise HTTPException(status_code=400, detail="Private jet is not available")
    data = booking_in.model_dump()
    # normalize booking datetimes to UTC naive
    for k in ("start_time", "end_time"):
        if data.get(k):
            dt = data[k]
            if isinstance(dt, datetime) and dt.tzinfo is not None:
                data[k] = dt.astimezone(timezone.utc).replace(tzinfo=None)
    start = data["start_time"]
    end = data["end_time"]
    if end <= start:
        raise HTTPException(status_code=400, detail="end_time must be after start_time")

    # simple pricing: hours * price_per_hour
    duration = (end - start).total_seconds() / 3600.0
    price = round(duration * (pj.price_per_hour or 0.0), 2)

    booking = PrivateJetBooking(
        user_id=current_user.id,
        private_jet_id=jet_id,
        start_time=start,
        end_time=end,
        price_paid=price,
    )
    pj.is_available = False
    db.add(booking)
    await db.commit()
    await db.refresh(booking)
    return booking


@privatejet_router.delete("/{booking_id}/cancel", response_model=dict)
async def cancel_private_jet_booking(
    booking_id: int,
    current_user: User = Depends(get_current_logged_user),
    db: AsyncSession = Depends(get_db),
):
    """Cancel a private jet booking and make the jet available again."""
    result = await db.execute(
        select(PrivateJetBooking).where(
            (PrivateJetBooking.id == booking_id) & (PrivateJetBooking.user_id == current_user.id)
        )
    )
    booking = result.scalar_one_or_none()
    if not booking:
        raise HTTPException(status_code=404, detail="Private jet booking not found")

    # Fetch and lock the jet
    jet_result = await db.execute(
        select(PrivateJet).where(PrivateJet.id == booking.private_jet_id).with_for_update()
    )
    jet = jet_result.scalar_one_or_none()
    if not jet:
        raise HTTPException(status_code=404, detail="Private jet not found")

    # Set jet back to available
    jet.is_available = True

    # Delete the booking
    await db.delete(booking)
    await db.commit()

    return {"message": f"Private jet booking {booking_id} cancelled successfully. Jet is now available."}

@router.get("/", response_model=List[FlightResponse])
async def get_all_flights(background_tasks: BackgroundTasks,
                          current_user: User = Depends(get_current_logged_user),
                          skip:int=0,
                          limit:int=10,
                          db: AsyncSession = Depends(get_db)):

    
    cached_flights = await redis_client.get("flights_cache")
    if cached_flights:
        print("---------------RETRIEVING DATA FROM REDIS CACHE!---------------")
        return json.loads(cached_flights)

    print("-------------RETRIEVING DATA FROM DATABASE!--------------")

    result = await db.execute(select(Flight))
    flights = result.scalars().all()
    flights_data = [FlightResponse.model_validate(f).model_dump() for f in flights]
    # Convert datetimes to ISO strings so they can be JSON serialized for Redis
    for fd in flights_data:
        for dt_key in ("departure_time", "arrival_time"):
            if dt_key in fd and fd[dt_key] is not None:
                val = fd[dt_key]
                if isinstance(val, datetime):
                    fd[dt_key] = val.isoformat()

    if flights_data:
        await redis_client.setex("flights_cache", 60, json.dumps(flights_data))
    paginated_flights = flights_data[skip : skip + limit]

    background_tasks.add_task(
        log_user_activity,
        user_id=current_user.id,
        action="SEARCH_ALL_FLIGHT",
        details={
                "number_of_flights_returned": len(paginated_flights),
                "BY": current_user.name
        }
    )

    return paginated_flights


@router.post("/", response_model=FlightResponse)
async def create_flight(
    flight: FlightCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    data = flight.model_dump()
    # normalize datetimes: convert aware datetimes to UTC naive
    for k in ("departure_time", "arrival_time"):
        if data.get(k):
            dt = data[k]
            if isinstance(dt, datetime) and dt.tzinfo is not None:
                data[k] = dt.astimezone(timezone.utc).replace(tzinfo=None)

    # validate segment_prices when stops are provided
    stops = data.get("stops") or []
    seg_prices = data.get("segment_prices")
    if stops:
        expected = len(stops) + 1
        if not seg_prices or len(seg_prices) != expected:
            raise HTTPException(status_code=400, detail=f"segment_prices must be provided with {expected} entries when stops are set")
        # basic shape validation
        for sp in seg_prices:
            if not all(k in sp for k in ("from_location", "to_location", "business", "premium", "economy")):
                raise HTTPException(status_code=400, detail="each segment_prices item must include from_location, to_location, business, premium, economy keys")

    # Validate seat counts (prevent creating too many seat records)
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

    # populate individual seat records based on the counts in the flight
    # use batch inserts to avoid memory issues
    batch_size = 1000
    seats_to_add = []
    
    for i in range(new_flight.business_seats or 0):
        seats_to_add.append(Seat(flight_id=new_flight.id, seat_number=f"B{i+1}", seat_type="business", is_booked=False))
        if len(seats_to_add) >= batch_size:
            db.add_all(seats_to_add)
            await db.flush()
            seats_to_add = []
    
    for i in range(new_flight.premium_seats or 0):
        seats_to_add.append(Seat(flight_id=new_flight.id, seat_number=f"P{i+1}", seat_type="premium", is_booked=False))
        if len(seats_to_add) >= batch_size:
            db.add_all(seats_to_add)
            await db.flush()
            seats_to_add = []
    
    for i in range(new_flight.economy_seats or 0):
        seats_to_add.append(Seat(flight_id=new_flight.id, seat_number=f"E{i+1}", seat_type="economy", is_booked=False))
        if len(seats_to_add) >= batch_size:
            db.add_all(seats_to_add)
            await db.flush()
            seats_to_add = []
    
    if seats_to_add:
        db.add_all(seats_to_add)
        await db.flush()
    
    await db.commit()

    await redis_client.delete("flights_cache")
    background_tasks.add_task(
        log_user_activity,
        user_id=current_user.id,
        action="CREATE_FLIGHT",
        details={
            "flight_id": new_flight.id,
            "source": new_flight.source,
            "destination": new_flight.destination,
            "BY":current_user.name
        }
    )
    return new_flight






# helper: compute price for a passenger's destination using per-segment prices if available
def _compute_price_for_destination(flight: Flight, seat_type: str, destination: str) -> float:
    # build route: source -> stops... -> destination
    route = [flight.source] + (flight.stops or []) + [flight.destination]
    try:
        dest_index = route.index(destination)
    except ValueError:
        return getattr(flight, f"{seat_type}_price") or 0.0

    # need segment_prices list with length == len(route)-1
    segs = flight.segment_prices if getattr(flight, "segment_prices", None) else None
    if not segs or len(segs) != len(route) - 1:
        # fallback to whole-flight price
        return getattr(flight, f"{seat_type}_price") or 0.0

    total = 0.0
    for i in range(dest_index):
        seg = segs[i]
        # price key matches seat_type
        price = seg.get(seat_type)
        if price is None:
            return getattr(flight, f"{seat_type}_price") or 0.0
        total += float(price)
    return total


@router.get("/{flight_id}/seats", response_model=List[SeatResponse])
async def get_flight_seats(
    flight_id: int,
    available: bool = True,
    db: AsyncSession = Depends(get_db),
):
    """Return seats for a flight.  Query parameter `available` filters by unbooked seats."""
    query = select(Seat).where(Seat.flight_id == flight_id)
    if available:
        query = query.where(Seat.is_booked == False)
    result = await db.execute(query)
    return result.scalars().all()





@router.post("/{flight_id}/book", response_model=List[BookingResponse])
async def book_flight(
    flight_id: int,
    booking_in: BookingCreate,
    background_tasks: BackgroundTasks, 
    current_user: User = Depends(get_current_logged_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Book specific seats for one or more passengers on a flight.
    """
    if not booking_in.passengers:
        raise HTTPException(status_code=400, detail="At least one passenger is required")

    result = await db.execute(
        select(Flight).where(Flight.id == flight_id).with_for_update()
    )
    flight = result.scalar_one_or_none()

    if not flight:
        raise HTTPException(status_code=404, detail="Flight not found")

    # validate route destinations
    allowed_destinations = []
    if flight.stops:
        allowed_destinations.extend(flight.stops)
    allowed_destinations.append(flight.destination)

    bookings = []
    for passenger in booking_in.passengers:
        if not passenger.destination:
            raise HTTPException(status_code=400, detail="Each passenger must include a destination on this flight route")
        if passenger.destination not in allowed_destinations:
            raise HTTPException(status_code=400, detail=f"Destination '{passenger.destination}' is not on this flight route")

        if not passenger.seat_number:
            raise HTTPException(status_code=400, detail="Each passenger must select a seat_number")

        # lock the seat record to avoid races
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
            raise HTTPException(status_code=400, detail=f"Seat {passenger.seat_number} is a {seat.seat_type} seat, not {passenger.seat_type}")

        # mark seat as booked
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

        # optionally decrement the denormalized counts to stay in sync
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
            "Booked_By":current_user.name
        }
    )

    return bookings




@router.get("/search", response_model=List[FlightResponse])
async def search_flights(
    background_tasks: BackgroundTasks,
    source: Optional[str] = None,
    destination: Optional[str] = None,
    departure_date: Optional[str] = None,  # YYYY-MM-DD
    price_max: Optional[float] = None,
    seat_class: Optional[Literal["business","premium","economy"]] = None,
    db: AsyncSession = Depends(get_db),
):
    filters = []
    if source:
        # Match flights that either start from this source or have it as a stop
        filters.append(
            (Flight.source == source) | (cast(Flight.stops, String).ilike(f'%{source}%'))
        )
    if destination:
        # Match flights that either go to this destination or have it as a stop
        filters.append(
            (Flight.destination == destination) | (cast(Flight.stops, String).ilike(f'%{destination}%'))
        )
    if departure_date:
        try:
            dt = datetime.fromisoformat(departure_date).date()
            filters.append(func.date(Flight.departure_time) == dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="departure_date must be YYYY-MM-DD")
    if price_max is not None and seat_class in ("business", "premium", "economy"):
        col = getattr(Flight, f"{seat_class}_price")
        filters.append(col <= price_max)


    if filters:
        query = select(Flight).where(and_(*filters))
    else:
        query = select(Flight)

    result = await db.execute(query)
    flights = result.scalars().all()

    for f in flights:
        background_tasks.add_task(
            increment_flight_analytics, 
            flight_id=f.id, 
            metric_name="search_count"
        )

    return [FlightResponse.model_validate(f).model_dump() for f in flights]


@router.put("/{flight_id}", response_model=FlightResponse)
async def update_flight(
    flight_id: int,
    flight_in: FlightCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Flight).where(Flight.id == flight_id).with_for_update()
    )
    flight = result.scalar_one_or_none()
    if not flight:
        raise HTTPException(status_code=404, detail="Flight not found")

    for k, v in flight_in.model_dump().items():
        # normalize datetime fields on update as well
        if v and k in ("departure_time", "arrival_time") and isinstance(v, datetime) and v.tzinfo is not None:
            v = v.astimezone(timezone.utc).replace(tzinfo=None)
        setattr(flight, k, v)

    # validate segment_prices when stops are present
    stops = flight.stops or []
    seg_prices = getattr(flight, "segment_prices", None)
    if stops:
        expected = len(stops) + 1
        if not seg_prices or len(seg_prices) != expected:
            raise HTTPException(status_code=400, detail=f"segment_prices must be provided with {expected} entries when stops are set")
        for sp in seg_prices:
            if not all(k in sp for k in ("from_location", "to_location", "business", "premium", "economy")):
                raise HTTPException(status_code=400, detail="each segment_prices item must include from_location, to_location, business, premium, economy keys")

    await db.commit()
    await db.refresh(flight)

    # if seat counts were increased, add new seat records (downgrades/removals are left to admin)
    seats_to_add = []
    # count existing seats per class
    existing = await db.execute(select(Seat).where(Seat.flight_id == flight.id))
    existing_seats = existing.scalars().all()
    counts = {"business": 0, "premium": 0, "economy": 0}
    for s in existing_seats:
        counts[s.seat_type] += 1

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
        details={
            "flight_id": flight_id,
            "updated_fields": list(flight_in.model_dump().keys()),
            "BY":current_user.name
        }
    )

    return flight


@router.delete("/{flight_id}")
async def delete_flight(
    flight_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Flight).where(Flight.id == flight_id))
    flight = result.scalar_one_or_none()
    if not flight:
        raise HTTPException(status_code=404, detail="Flight not found")
    
    background_tasks.add_task(
        log_user_activity,
        user_id=current_user.id,
        action="DELETE_FLIGHT",
        details={
            "flight_id": flight_id,
            "BY":current_user.name
        }
    )

    await db.delete(flight)
    await db.commit()
    await redis_client.delete("flights_cache")
    return {"message": "Flight deleted"}


@bookings_router.get("/", response_model=List[BookingResponse])
async def get_user_bookings(
    skip: int = 0,
    limit: int = 10,
    current_user: User = Depends(get_current_logged_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Booking)
        .where(Booking.user_id == current_user.id)
        .offset(skip)
        .limit(limit)
    )
    bookings = result.scalars().all()
    return bookings


@bookings_router.get("/{booking_id}", response_model=BookingResponse)
async def get_booking(
    booking_id: int,
    current_user: User = Depends(get_current_logged_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Booking).where((Booking.id == booking_id) & (Booking.user_id == current_user.id))
    )
    booking = result.scalar_one_or_none()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking


@bookings_router.delete("/{booking_id}")
async def cancel_booking(
    booking_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_logged_user),
    db: AsyncSession = Depends(get_db),
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

    # free up seat record if we have one
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

    # update denormalized counters if used
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
            "BY":current_user.name
        }
    )

    return {"message": "Booking cancelled successfully"}


""" {
  "source": "Delhi",
  "destination": "Mumbai",
  "stops": ["Jaipur","Indore"],
  "segment_prices": [
    {
      "from_location": "Delhi",
      "to_location": "Jaipur",
      "business": 2500,
      "premium": 1800,
      "economy": 900
    },
    {
      "from_location": "Jaipur",
      "to_location": "Indore",
      "business": 2000,
      "premium": 1500,
      "economy": 700
    },
    {
      "from_location": "Indore",
      "to_location": "Mumbai",
      "business": 3000,
      "premium": 2200,
      "economy": 1200
    }
  ],
  "business_price": 5000,
  "premium_price": 3500,
  "economy_price": 2000,
  "business_seats": 10,
  "premium_seats": 20,
  "economy_seats": 50,
  "departure_time": "2026-03-01T10:00:00",
  "arrival_time": "2026-03-01T18:00:00",
  "airline": "Air India"
} """