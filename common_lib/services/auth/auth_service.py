import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from sqlmodel import Session

from common_lib.database.database import get_session
from common_lib.services.crud import user as UserService
from common_lib.models import User
from .cookieauth import OAuth2PasswordBearerWithCookie
from common_lib.database.config import get_settings
from ...models.User import RoleEnum

settings = get_settings()
oauth2_scheme = OAuth2PasswordBearerWithCookie(tokenUrl="/api/auth/token", auto_error=False)

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
logger = logging.getLogger(__name__)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme),
    session: Session = Depends(get_session)
) -> Optional[User]:
    if token is None:
        logger.debug("No token provided for optional authentication.")
        return None

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: Optional[str] = payload.get("sub")
        if email is None:
            logger.warning("Token payload missing 'sub' (email).")
            return None
    except JWTError as e:
        logger.warning(f"JWTError during optional token decode: {e}")
        return None
    user = UserService.get_user_by_email(email=email, session=session)
    if user is None:
        logger.warning(f"User not found for email in optional token: {email}")
        return None
    logger.debug(f"Successfully authenticated optional user: {user.email}")
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user_optional)):
    if current_user is None:
        logger.info("Mandatory authentication failed (checked cookie). Raising 401.")
        return None
    logger.info(f"Mandatory authentication successful for user: {current_user.email} -- {current_user.role}")
    return current_user


def require_role(required_role: RoleEnum):
    def _check_role(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
            )
        if required_role != current_user.role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Недостаточно прав. Требуется роль: {required_role.value}"
            )
        return current_user

    return _check_role
