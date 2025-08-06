from datetime import timedelta
from uuid import UUID

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session
from starlette.responses import Response, RedirectResponse
from common_lib.database.config import get_settings
from common_lib.database.database import get_session
from common_lib.models import User, UserCreate, UserOut
from common_lib.services.crud import user as UserService
import common_lib.services.auth.auth_service as AuthService
from typing import List, Dict
import logging


settings = get_settings()
logger = logging.getLogger(__name__)

user_route = APIRouter()


@user_route.post(
    '/register',
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    summary="User Registration",
    description="Register a new user with name, email and password."
)
async def register(user_data: UserCreate, session: Session = Depends(get_session)) -> UserOut:
    logger.info(f"Registration attempt for user: {user_data}")
    db_user = UserService.get_user_by_email(session=session, email=user_data.email)
    if db_user:
        logger.warning(f"Registration failed: Email already exists {user_data.email}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )
    try:
        created_user = UserService.create_user(session=session, user_in=user_data)
        logger.info(f"User registered successfully: {created_user.email}")
        return UserOut.from_orm(created_user)
    except Exception as e:
        logger.error(f"Error during user registration: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during registration.",
        )


@user_route.post(
    '/token',
    response_model=Dict[str, str],
    summary="Create Access Token",
    description="Login for existing user using form data, sets access token in cookie."
)
async def login_for_access_token( response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session)
):
    logger.info(f"Login attempt for user: {form_data.username}")
    user = UserService.authenticate_user(
        session=session, email=form_data.username, password=form_data.password
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = AuthService.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    response.set_cookie(
        key=settings.COOKIE_NAME,
        value=f"Bearer {access_token}",
        httponly=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        expires=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax",
        secure=True,
    )
    logger.info(f"Cookie set for user: {user.email}")
    return {"message": "Login successful","user_id": str(user.id)}


@user_route.get(
    "/users/{user_id}",
    response_model=UserOut,
    summary="Get User by ID",
    description="Returns user information by user ID",
)
async def get_user_by_id(
    user_id: UUID,
    session: Session = Depends(get_session)
):
    user = UserService.get_user_by_id(session=session, user_id=user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return user

@user_route.post(
    '/logout',
    response_model=Dict[str, str],
    summary="User Logout",
    description="Clears the authentication cookie."
)
async def logout(response: Response):
    logger.info("Logout request received.")
    response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    logger.info(f"Attempting to delete cookie: {settings.COOKIE_NAME}")
    response.delete_cookie(
        key=settings.COOKIE_NAME,
        secure=True,
        httponly=True,
        samesite="lax",
    )

    logger.info(f"Cookie {settings.COOKIE_NAME} deletion initiated, redirecting to /.")
    return response



@user_route.get(
    "/users",
    response_model=List[UserOut],
    summary="Get all users",
    response_description="List of all users"
)
async def get_all_users(session=Depends(get_session)) -> List[UserOut]:
    try:
        users = UserService.get_all_users(session)
        logger.info(f"Retrieved {len(users)} users")
        return users
    except Exception as e:
        logger.error(f"Error retrieving users: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving users"
        )