"""Test suite for the user_routes FastAPI endpoints."""

import uuid
from typing import Dict

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import app.routers.user_routes as user_routes
from app.routers.user_routes import router
from app.dependencies import get_current_user, get_db, get_email_service
from app.models.user_model import UserRole
from app.services.user_service import UserService


DUMMY_ID = str(uuid.uuid4())
DUMMY_DATA: Dict[str, object] = {
    "id": DUMMY_ID,
    "nickname": "nick",
    "first_name": "First",
    "last_name": "Last",
    "bio": "Bio",
    "profile_picture_url": "pic_url",
    "github_profile_url": "gh_url",
    "linkedin_profile_url": "li_url",
    "role": UserRole.ADMIN,
    "email": "test@example.com",
    "last_login_at": "2025-05-01T12:00:00Z",
    "created_at": "2025-05-01T10:00:00Z",
    "updated_at": "2025-05-01T11:00:00Z",
    "is_professional": False,
}


class DummyUser:
    """Minimal stub for a user-like object with attributes."""

    def __init__(self, **kwargs: object) -> None:
        for key, value in kwargs.items():
            setattr(self, key, value)


dummy_user = DummyUser(**DUMMY_DATA)


def auth_headers() -> Dict[str, str]:
    """Return a fake Authorization header for testing."""
    return {"Authorization": "Bearer faketoken"}



@pytest.fixture(scope="module")
def app() -> FastAPI:
    """Create a FastAPI app instance with dependency overrides."""
    testing_app = FastAPI()
    testing_app.include_router(router)

    # Stub get_current_user to always return an ADMIN
    def _fake_current_user() -> Dict[str, object]:
        return {"user_id": DUMMY_ID, "role": "ADMIN"}

    testing_app.dependency_overrides[get_current_user] = _fake_current_user
    testing_app.dependency_overrides[get_db] = lambda: None
    testing_app.dependency_overrides[get_email_service] = lambda: None

    return testing_app


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    """TestClient for the FastAPI app."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def stub_links(monkeypatch) -> None:
    """Stub out link-generation functions for deterministic output."""
    monkeypatch.setattr(
        user_routes,
        "create_user_links",
        lambda uid, req: {"self": f"/users/{uid}"},
    )
    monkeypatch.setattr(
        user_routes,
        "generate_pagination_links",
        lambda req, skip, limit, total: {"self": f"/users?skip={skip}&limit={limit}"},
    )


def test_set_professional_status_not_found(client: TestClient, monkeypatch) -> None:
    """PATCH /users/{id}/professional returns 404 if user not found."""
    async def _stub_update(db, uid, data):
        return None

    monkeypatch.setattr(UserService, "update", _stub_update)
    response = client.patch(
        f"/users/{DUMMY_ID}/professional",
        json={"is_professional": True},
        headers=auth_headers(),
    )
    assert response.status_code == 404



def test_get_user_success(client: TestClient, monkeypatch) -> None:
    """GET /users/{id} returns 200 and the correct id."""
    async def _stub_get_by_id(db, uid):
        return dummy_user

    monkeypatch.setattr(UserService, "get_by_id", _stub_get_by_id)
    response = client.get(
        f"/users/{DUMMY_ID}",
        headers=auth_headers(),
    )
    assert response.status_code == 200
    assert response.json().get("id") == DUMMY_DATA["id"]


def test_get_user_not_found(client: TestClient, monkeypatch) -> None:
    """GET /users/{id} returns 404 when user not found."""
    async def _stub_get_by_id(db, uid):
        return None

    monkeypatch.setattr(UserService, "get_by_id", _stub_get_by_id)
    response = client.get(
        f"/users/{DUMMY_ID}",
        headers=auth_headers(),
    )
    assert response.status_code == 404


def test_update_user_success(client: TestClient, monkeypatch) -> None:
    """PUT /users/{id} updates bio successfully."""
    async def _stub_update(db, uid, data):
        updated = DUMMY_DATA.copy()
        updated.update(data)
        return DummyUser(**updated)

    monkeypatch.setattr(UserService, "update", _stub_update)
    response = client.put(
        f"/users/{DUMMY_ID}",
        json={"bio": "updated"},
        headers=auth_headers(),
    )
    assert response.status_code == 200
    assert response.json().get("bio") == "updated"


def test_update_user_not_found(client: TestClient, monkeypatch) -> None:
    """PUT /users/{id} returns 404 when user not found."""
    async def _stub_update(db, uid, data):
        return None

    monkeypatch.setattr(UserService, "update", _stub_update)
    response = client.put(
        f"/users/{DUMMY_ID}",
        json={"bio": "updated"},
        headers=auth_headers(),
    )
    assert response.status_code == 404


def test_delete_user_success(client: TestClient, monkeypatch) -> None:
    """DELETE /users/{id} returns 204 on success."""
    async def _stub_delete(db, uid):
        return True

    monkeypatch.setattr(UserService, "delete", _stub_delete)
    response = client.delete(
        f"/users/{DUMMY_ID}",
        headers=auth_headers(),
    )
    assert response.status_code == 204


def test_delete_user_not_found(client: TestClient, monkeypatch) -> None:
    """DELETE /users/{id} returns 404 when user not found."""
    async def _stub_delete(db, uid):
        return False

    monkeypatch.setattr(UserService, "delete", _stub_delete)
    response = client.delete(
        f"/users/{DUMMY_ID}",
        headers=auth_headers(),
    )
    assert response.status_code == 404



def test_create_user_success(client: TestClient, monkeypatch) -> None:
    """POST /users/ returns 201 and correct email when new."""
    async def _stub_get_by_email(db, email):
        return None

    async def _stub_create(db, data, svc):
        return dummy_user

    monkeypatch.setattr(UserService, "get_by_email", _stub_get_by_email)
    monkeypatch.setattr(UserService, "create", _stub_create)

    payload = {
        "email": DUMMY_DATA["email"],
        "password": "Pass1234!",
        "role": DUMMY_DATA["role"].value,
    }
    response = client.post(
        "/users/",
        json=payload,
        headers=auth_headers(),
    )
    assert response.status_code == 201
    assert response.json().get("email") == DUMMY_DATA["email"]


def test_create_user_existing_email(client: TestClient, monkeypatch) -> None:
    """POST /users/ returns 400 when email already exists."""
    async def _stub_get_by_email(db, email):
        return dummy_user

    monkeypatch.setattr(UserService, "get_by_email", _stub_get_by_email)

    payload = {
        "email": DUMMY_DATA["email"],
        "password": "Pass1234!",
        "role": DUMMY_DATA["role"].value,
    }
    response = client.post(
        "/users/",
        json=payload,
        headers=auth_headers(),
    )
    assert response.status_code == 400




def test_register_duplicate(client: TestClient, monkeypatch) -> None:
    """POST /register/ returns 400 when email is duplicate."""
    async def _stub_register(db, data, svc):
        return None

    monkeypatch.setattr(UserService, "register_user", _stub_register)

    payload = {
        "email": DUMMY_DATA["email"],
        "password": "Pass1234!",
        "role": DUMMY_DATA["role"].value,
    }
    response = client.post("/register/", json=payload)
    assert response.status_code == 400


def test_login_success(client: TestClient, monkeypatch) -> None:
    """POST /login/ returns token on valid credentials."""
    async def _stub_locked(db, user):
        return False

    async def _stub_login(db, u, p):
        return dummy_user

    monkeypatch.setattr(UserService, "is_account_locked", _stub_locked)
    monkeypatch.setattr(UserService, "login_user", _stub_login)

    response = client.post(
        "/login/",
        data={"username": DUMMY_DATA["email"], "password": "Pass1234!"},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_login_locked(client: TestClient, monkeypatch) -> None:
    """POST /login/ returns 400 when account is locked."""
    async def _stub_locked(db, user):
        return True

    monkeypatch.setattr(UserService, "is_account_locked", _stub_locked)

    response = client.post(
        "/login/",
        data={"username": DUMMY_DATA["email"], "password": "Pass1234!"},
    )
    assert response.status_code == 400


def test_login_incorrect(client: TestClient, monkeypatch) -> None:
    """POST /login/ returns 401 on bad credentials."""
    async def _stub_locked(db, user):
        return False

    async def _stub_login(db, u, p):
        return None

    monkeypatch.setattr(UserService, "is_account_locked", _stub_locked)
    monkeypatch.setattr(UserService, "login_user", _stub_login)

    response = client.post(
        "/login/",
        data={"username": DUMMY_DATA["email"], "password": "Pass1234!"},
    )
    assert response.status_code == 401

def test_verify_email_success(client: TestClient, monkeypatch) -> None:
    """GET /verify-email/{id}/{token} returns 200 when token is valid."""
    async def _stub_verify(db, uid, tok):
        return True

    monkeypatch.setattr(UserService, "verify_email_with_token", _stub_verify)

    response = client.get(f"/verify-email/{DUMMY_ID}/sometoken")
    assert response.status_code == 200


def test_verify_email_invalid(client: TestClient, monkeypatch) -> None:
    """GET /verify-email/{id}/{token} returns 400 when token is invalid."""
    async def _stub_verify(db, uid, tok):
        return False

    monkeypatch.setattr(UserService, "verify_email_with_token", _stub_verify)

    response = client.get(f"/verify-email/{DUMMY_ID}/sometoken")
    assert response.status_code == 400
