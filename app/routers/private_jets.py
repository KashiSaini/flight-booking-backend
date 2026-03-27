from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.db.postgres import get_db
from app.models.user import User
from app.schemas.private_jet import (
    PrivateJetCreate,
    PrivateJetResponse,
    PrivateJetBookingCreate,
    PrivateJetBookingResponse,
)
from app.api.dependencies.auth import get_current_logged_user, get_admin_user
from app.services import private_jet_service

privatejet_router = APIRouter(prefix="/private-jets", tags=["Private Jets"])


@privatejet_router.post("/", response_model=PrivateJetResponse)
async def create_private_jet(
    jet_in: PrivateJetCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_admin_user),
):
    return await private_jet_service.create_private_jet(
        jet_in=jet_in,
        db=db,
        current_user=current_user,
    )


@privatejet_router.get("/", response_model=List[PrivateJetResponse])
async def list_private_jets(
    available: Optional[bool] = True,
    db: AsyncSession = Depends(get_db),
):
    return await private_jet_service.list_private_jets(
        available=available,
        db=db,
    )


@privatejet_router.post("/{jet_id}/book", response_model=PrivateJetBookingResponse)
async def book_private_jet(
    jet_id: int,
    booking_in: PrivateJetBookingCreate,
    current_user: User = Depends(get_current_logged_user),
    db: AsyncSession = Depends(get_db),
):
    return await private_jet_service.book_private_jet(
        jet_id=jet_id,
        booking_in=booking_in,
        current_user=current_user,
        db=db,
    )


@privatejet_router.delete("/{booking_id}/cancel", response_model=dict)
async def cancel_private_jet_booking(
    booking_id: int,
    current_user: User = Depends(get_current_logged_user),
    db: AsyncSession = Depends(get_db),
):
    return await private_jet_service.cancel_private_jet_booking(
        booking_id=booking_id,
        current_user=current_user,
        db=db,
    )