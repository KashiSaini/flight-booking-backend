from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from shared.db.postgres import get_db
from shared.models.user import User
from shared.security import get_current_user_from_token

security = HTTPBearer()

async def get_current_logged_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    token = credentials.credentials
    return await get_current_user_from_token(token, db)

async def get_admin_user(current_user: User = Depends(get_current_logged_user)):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only Admin users can access this resource",
        )
    return current_user
