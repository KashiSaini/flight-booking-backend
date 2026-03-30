from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.private_jet import PrivateJetBookingCreate, PrivateJetCreate
from shared.models.private_jet import PrivateJet, PrivateJetBooking
from shared.models.user import User

async def create_private_jet(jet_in: PrivateJetCreate, db: AsyncSession, current_user: User):
    data = jet_in.model_dump()
    for key in ("available_from", "available_to"):
        if data.get(key):
            dt = data[key]
            if isinstance(dt, datetime) and dt.tzinfo is not None:
                data[key] = dt.astimezone(timezone.utc).replace(tzinfo=None)

    private_jet = PrivateJet(**data, owner_id=current_user.id)
    db.add(private_jet)
    await db.commit()
    await db.refresh(private_jet)
    return private_jet

async def list_private_jets(available: Optional[bool], db: AsyncSession):
    query = select(PrivateJet)
    if available:
        query = query.where(PrivateJet.is_available == True)
    result = await db.execute(query)
    return result.scalars().all()

async def book_private_jet(jet_id: int, booking_in: PrivateJetBookingCreate, current_user: User, db: AsyncSession):
    result = await db.execute(select(PrivateJet).where(PrivateJet.id == jet_id).with_for_update())
    private_jet = result.scalar_one_or_none()
    if not private_jet:
        raise HTTPException(status_code=404, detail="Private jet not found")
    if not private_jet.is_available:
        raise HTTPException(status_code=400, detail="Private jet is not available")

    data = booking_in.model_dump()
    for key in ("start_time", "end_time"):
        if data.get(key):
            dt = data[key]
            if isinstance(dt, datetime) and dt.tzinfo is not None:
                data[key] = dt.astimezone(timezone.utc).replace(tzinfo=None)

    start = data["start_time"]
    end = data["end_time"]
    if end <= start:
        raise HTTPException(status_code=400, detail="end_time must be after start_time")

    duration = (end - start).total_seconds() / 3600.0
    price = round(duration * (private_jet.price_per_hour or 0.0), 2)

    booking = PrivateJetBooking(
        user_id=current_user.id,
        private_jet_id=jet_id,
        start_time=start,
        end_time=end,
        price_paid=price,
    )
    private_jet.is_available = False
    db.add(booking)
    await db.commit()
    await db.refresh(booking)
    return booking

async def cancel_private_jet_booking(booking_id: int, current_user: User, db: AsyncSession):
    result = await db.execute(
        select(PrivateJetBooking).where(
            (PrivateJetBooking.id == booking_id) & (PrivateJetBooking.user_id == current_user.id)
        )
    )
    booking = result.scalar_one_or_none()
    if not booking:
        raise HTTPException(status_code=404, detail="Private jet booking not found")

    jet_result = await db.execute(select(PrivateJet).where(PrivateJet.id == booking.private_jet_id).with_for_update())
    private_jet = jet_result.scalar_one_or_none()
    if not private_jet:
        raise HTTPException(status_code=404, detail="Private jet not found")

    private_jet.is_available = True
    await db.delete(booking)
    await db.commit()
    return {"message": f"Private jet booking {booking_id} cancelled successfully. Jet is now available."}
