from fastapi import APIRouter, Depends, Body, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_logged_user, get_admin_user
from app.db.postgres import get_db
from app.models.user import User
from app.schemas.auth import UserCreate, UserResponse, LoginRequest
from app.services import auth_service

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserResponse)
async def register(user: UserCreate, db: AsyncSession = Depends(get_db)):
    return await auth_service.register_user(user=user, db=db)


@router.post("/login")
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    return await auth_service.login_user(data=data, db=db)


@router.post("/refresh")
async def refresh_token(refresh_token: str = Body(...)):
    return await auth_service.refresh_access_token(refresh_token)


@router.post("/logout")
async def logout(
    request: Request,
    token: str = Depends(oauth2_scheme),
    current_user: User = Depends(get_current_logged_user)
):
    return await auth_service.logout_user(current_user=current_user, token=token)


@router.post("/promote-admin/{user_id}", response_model=UserResponse)
async def promote_to_admin(
    user_id: int,
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    return await auth_service.promote_user_to_admin(user_id=user_id, db=db)


@router.get("/get_users", response_model=list[UserResponse])
async def get_users(
    current_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    return await auth_service.get_all_users(db=db)