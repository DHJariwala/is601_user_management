"""
Test suite for User Profile Management feature.

Covers:
- GET and PATCH /users/me for ADMIN and MANAGER roles.
- Forbidden behavior for AUTHENTICATED users on /users/me.
- PATCH /users/{id}/professional for professional status management.
"""
import pytest


@pytest.mark.asyncio
async def test_get_current_user_success_for_admin(async_client, admin_user, admin_token):
    """
    ADMIN can fetch their own profile via GET /users/me.
    """
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = await async_client.get("/users/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(admin_user.id)
    assert data["role"] == "ADMIN"


@pytest.mark.asyncio
async def test_get_current_user_success_for_manager(async_client, manager_user, manager_token):
    """
    MANAGER can fetch their own profile via GET /users/me.
    """
    headers = {"Authorization": f"Bearer {manager_token}"}
    response = await async_client.get("/users/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(manager_user.id)
    assert data["role"] == "MANAGER"


@pytest.mark.asyncio
async def test_get_current_user_forbidden_for_authenticated_user(async_client, user, user_token):
    """
    AUTHENTICATED user should be forbidden from fetching /users/me.
    """
    _ = user
    headers = {"Authorization": f"Bearer {user_token}"}
    response = await async_client.get("/users/me", headers=headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_update_current_user_success_for_admin(async_client, admin_user, admin_token):
    """
    ADMIN can update their own profile via PATCH /users/me.
    """
    headers = {"Authorization": f"Bearer {admin_token}"}
    payload = {"bio": "Updated by admin"}
    response = await async_client.patch("/users/me", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["bio"] == "Updated by admin"


@pytest.mark.asyncio
async def test_update_current_user_success_for_manager(async_client, manager_user, manager_token):
    """
    MANAGER can update their own profile via PATCH /users/me.
    """
    headers = {"Authorization": f"Bearer {manager_token}"}
    payload = {"bio": "Manager update"}
    response = await async_client.patch("/users/me", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["bio"] == "Manager update"


@pytest.mark.asyncio
async def test_update_current_user_forbidden_for_authenticated_user(async_client, user, user_token):
    """
    AUTHENTICATED user should be forbidden from updating /users/me.
    """
    _ = user
    headers = {"Authorization": f"Bearer {user_token}"}
    payload = {"bio": "Trying to escalate"}
    response = await async_client.patch("/users/me", json=payload, headers=headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_set_professional_status_by_admin(async_client, user, admin_token):
    """
    ADMIN can set professional status for any user via PATCH /users/{id}/professional.
    """
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = await async_client.patch(
        f"/users/{user.id}/professional", json={"is_professional": True}, headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_professional"] is True


@pytest.mark.asyncio
async def test_set_professional_status_by_manager(async_client, user, manager_token):
    """
    MANAGER can set professional status for any user via PATCH /users/{id}/professional.
    """
    headers = {"Authorization": f"Bearer {manager_token}"}
    response = await async_client.patch(
        f"/users/{user.id}/professional", json={"is_professional": True}, headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["is_professional"] is True


@pytest.mark.asyncio
async def test_set_professional_status_forbidden_for_authenticated_user(async_client, user, user_token):
    """
    AUTHENTICATED user should be forbidden from setting professional status.
    """
    headers = {"Authorization": f"Bearer {user_token}"}
    response = await async_client.patch(
        f"/users/{user.id}/professional", json={"is_professional": True}, headers=headers
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_set_professional_status_invalid_user(async_client, admin_token):
    """
    Setting professional status for non-existent user returns 404.
    """
    fake_id = "00000000-0000-0000-0000-000000000000"
    headers = {"Authorization": f"Bearer {admin_token}"}
    response = await async_client.patch(
        f"/users/{fake_id}/professional", json={"is_professional": True}, headers=headers
    )
    assert response.status_code == 404
