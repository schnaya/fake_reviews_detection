import logging
import uuid
from decimal import Decimal
from typing import Optional, List
from passlib.context import CryptContext

from sqlmodel import Session, select
from common_lib.models import User, UserCreate, UserOut
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_user(session: Session, user_in: UserCreate) -> UserOut:
    existing_user = get_user_by_email(session, user_in.email)
    if existing_user:
        logger.warning(f"Attempted to create user '{user_in.email}' which already exists.")
        raise ValueError(f"User with email {user_in.email} already exists")
        pass

    hashed_password = get_password_hash(user_in.password)
    db_user = User(
        email=user_in.email,
        hashed_password=hashed_password,
        name=user_in.name,
        role=user_in.role,
    )

    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    logger.info(f"User '{db_user.email}' created successfully with ID {db_user.id}")
    return UserOut.from_orm(db_user)


def get_user_by_id(session: Session, user_id: uuid.UUID) -> Optional[UserOut]:
    user = session.get(User, user_id)
    return UserOut.from_orm(user)


def get_user_by_email(session: Session, email: str) -> Optional[UserOut]:
    user = session.exec(select(User).where(User.email == email)).first()
    if not user:
        return None
    return UserOut.from_orm(user)


def get_user_by_email_raw(session: Session, email: str) -> Optional[User]:
    return session.exec(select(User).where(User.email == email)).first()


def get_all_users(session: Session) -> List[UserOut]:
    users = session.exec(select(User)).all()
    return [UserOut.from_orm(user) for user in users]


def authenticate_user(session: Session, email: str, password: str) -> Optional[UserOut]:
    user = get_user_by_email_raw(session, email)
    if not user:
        logger.warning(f"Authentication failed: User '{email}' not found.")
        return None
    if not verify_password(password, user.hashed_password):
        logger.warning(f"Authentication failed: Incorrect password for user '{email}'.")
        return None
    logger.info(f"User '{email}' authenticated successfully.")
    return UserOut.from_orm(user)


def ensure_user(session: Session, user: UserCreate) -> UserOut:
    existing_user = get_user_by_email(session, user.email)
    if not existing_user:
        logger.info(f"User '{user.email}' not found. Creating new user...")
        user = create_user(session=session, user_in=user)
        return user
    else:
        logger.info(f"User '{user.email}' already exists. Skipping creation.")
        return existing_user
