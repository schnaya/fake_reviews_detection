from fastapi.testclient import TestClient
from sqlmodel import Session
from common_lib.models import User


def test_user_registration_existing_email(client: TestClient, test_user: User):
    response = client.post(
        "/api/auth/register",
        json={"name": "Another User", "email": "test@example.com", "password": "password123"}
    )
    assert response.status_code == 409
    assert response.json()["detail"] == "Email already registered"


def test_user_login(client: TestClient, test_user: User):
    response = client.post(
        "/api/auth/token",
        data={"username": test_user.email, "password": "password123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Login successful"
    assert "set-cookie" in response.headers


def test_user_login_wrong_password(client: TestClient, test_user: User):
    response = client.post(
        "/api/auth/token",
        data={"username": test_user.email, "password": "wrongpassword"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"


def test_get_user_by_id(client: TestClient, test_user: User):
    response = client.get(f"/api/auth/users/{test_user.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == test_user.email
    assert data["id"] == str(test_user.id)