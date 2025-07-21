import logging
from sqlmodel import SQLModel, Session, create_engine
from .config import get_settings
from common_lib.models import UserCreate
from common_lib.services.crud.user import ensure_user
from ..services.crud.product import ensure_products

engine = create_engine(url=get_settings().DATABASE_URL_psycopg,
                       echo=False, pool_size=5, max_overflow=10)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


def get_session():
    with Session(engine) as session:
        yield session


def create_db_and_tables():
    logger.info("Attempting to create database tables...")
    try:
        SQLModel.metadata.create_all(engine)
        logger.info("Tables created successfully (or already exist).")
    except Exception as e:
        logger.error(f"Error creating tables: {e}", exc_info=True)
        raise


def init_db():
    create_db_and_tables()
    demo_user = UserCreate(
        name="Demo User",
        email="demo@example.com",
        password="demo123",
        role="user"
    )
    admin_user = UserCreate(
        name="Admin",
        email="admin@example.com",
        password="admin123",
        role="admin"
    )
    with Session(engine) as session:
        ensure_user(session, demo_user)
        ensure_user(session, admin_user)
        ensure_products(session)

