import pytest
from typing import Generator
from unittest.mock import patch, AsyncMock

from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine

from app.api import app
from common_lib.database.database import get_session
from common_lib.database.config import get_settings, Settings
from common_lib.models import User, Product, RoleEnum
from common_lib.services.auth.auth_service import create_access_token

TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})


def get_settings_override():
    return Settings(DATABASE_URL=TEST_DATABASE_URL)


@pytest.fixture(scope="session", autouse=True)
def override_app_settings():
    app.dependency_overrides[get_settings] = get_settings_override
    yield
    app.dependency_overrides.clear()


@pytest.fixture(scope="function", autouse=True)
def mocked_app_lifecycle():
    with patch("app.api.init_db", return_value=None), \
         patch("app.api.connect_rabbitmq", new_callable=AsyncMock), \
         patch("app.api.close_rabbitmq", new_callable=AsyncMock):
        yield


@pytest.fixture(scope="function")
def session() -> Generator[Session, None, None]:
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)


@pytest.fixture(scope="function")
def client(session: Session) -> Generator[TestClient, None, None]:
    def get_session_override():
        yield session

    app.dependency_overrides[get_session] = get_session_override

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_user(session: Session) -> User:
    from common_lib.services.crud.user import create_user
    from common_lib.models import UserCreate
    user_in = UserCreate(name="Test User", email="test@example.com", password="password123")
    return create_user(session=session, user_in=user_in)


@pytest.fixture(scope="function")
def test_admin_user(session: Session) -> User:
    from common_lib.services.crud.user import create_user
    from common_lib.models import UserCreate
    user_in = UserCreate(name="Admin", email="admin@example.com", password="adminpass", role=RoleEnum.ADMIN)
    return create_user(session=session, user_in=user_in)


@pytest.fixture(scope="function")
def authorized_client(client: TestClient, test_user: User) -> TestClient:
    token = create_access_token(data={"sub": test_user.email})
    client.headers = {"Authorization": f"Bearer {token}"}
    return client


@pytest.fixture(scope="function")
def admin_authorized_client(client: TestClient, test_admin_user: User) -> TestClient:
    token = create_access_token(data={"sub": test_admin_user.email})
    client.headers = {"Authorization": f"Bearer {token}"}
    return client


@pytest.fixture(scope="function")
def test_product(session: Session) -> Product:
    product = Product(
        name="Test Product",
        description="A great product",
        price=9.99
    )
    session.add(product)
    session.commit()
    session.refresh(product)
    return product

