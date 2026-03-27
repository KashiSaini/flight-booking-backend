from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List
from datetime import datetime, timezone

from app.models.private_jet import PrivateJet, PrivateJetBooking
from app.models.user import User
from app.schemas.private_jet import PrivateJetCreate, PrivateJetBookingCreate


async def create_private_jet(
    jet_in: PrivateJetCreate,
    db: AsyncSession,
    current_user: User,
):
    data = jet_in.model_dump()

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


async def list_private_jets(
    available: Optional[bool],
    db: AsyncSession,
):
    q = select(PrivateJet)
    if available:
        q = q.where(PrivateJet.is_available == True)

    res = await db.execute(q)
    return res.scalars().all()


async def book_private_jet(
    jet_id: int,
    booking_in: PrivateJetBookingCreate,
    current_user: User,
    db: AsyncSession,
):
    result = await db.execute(select(PrivateJet).where(PrivateJet.id == jet_id).with_for_update())
    pj = result.scalar_one_or_none()

    if not pj:
        raise HTTPException(status_code=404, detail="Private jet not found")

    if not pj.is_available:
        raise HTTPException(status_code=400, detail="Private jet is not available")

    data = booking_in.model_dump()

    for k in ("start_time", "end_time"):
        if data.get(k):
            dt = data[k]
            if isinstance(dt, datetime) and dt.tzinfo is not None:
                data[k] = dt.astimezone(timezone.utc).replace(tzinfo=None)

    start = data["start_time"]
    end = data["end_time"]

    if end <= start:
        raise HTTPException(status_code=400, detail="end_time must be after start_time")

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


async def cancel_private_jet_booking(
    booking_id: int,
    current_user: User,
    db: AsyncSession,
):
    result = await db.execute(
        select(PrivateJetBooking).where(
            (PrivateJetBooking.id == booking_id) & (PrivateJetBooking.user_id == current_user.id)
        )
    )
    booking = result.scalar_one_or_none()

    if not booking:
        raise HTTPException(status_code=404, detail="Private jet booking not found")

    jet_result = await db.execute(
        select(PrivateJet).where(PrivateJet.id == booking.private_jet_id).with_for_update()
    )
    jet = jet_result.scalar_one_or_none()

    if not jet:
        raise HTTPException(status_code=404, detail="Private jet not found")

    jet.is_available = True

    await db.delete(booking)
    await db.commit()

    return {
        "message": f"Private jet booking {booking_id} cancelled successfully. Jet is now available."
    }