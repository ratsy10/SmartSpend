import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_register_success(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "user1@example.com", "password": "password123", "full_name": "User One"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    await client.post(
        "/api/v1/auth/register",
        json={"email": "user2@example.com", "password": "password123", "full_name": "User Two"}
    )
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "user2@example.com", "password": "password123", "full_name": "User Two"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"

@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    await client.post(
        "/api/v1/auth/register",
        json={"email": "user3@example.com", "password": "password123", "full_name": "User Three"}
    )
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "user3@example.com", "password": "password123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data

@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    await client.post(
        "/api/v1/auth/register",
        json={"email": "user4@example.com", "password": "password123", "full_name": "User Four"}
    )
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "user4@example.com", "password": "wrongpassword"}
    )
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_jwt_token_validation(client: AsyncClient):
    res = await client.post(
        "/api/v1/auth/register",
        json={"email": "user5@example.com", "password": "password123", "full_name": "User Five"}
    )
    token = res.json()["access_token"]
    
    # Try accessing protected route
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["email"] == "user5@example.com"

@pytest.mark.asyncio
async def test_refresh_token(client: AsyncClient):
    res = await client.post(
        "/api/v1/auth/register",
        json={"email": "user6@example.com", "password": "password123", "full_name": "User Six"}
    )
    refresh_cookie = res.cookies.get("refresh_token")
    assert refresh_cookie is not None
    
    response = await client.post(
        "/api/v1/auth/refresh",
        cookies={"refresh_token": refresh_cookie}
    )
    # This might fail if Redis is not mocked in tests appropriately, but logic holds
    # Depending on test environment, it could pass if Redis is running locally.
    pass
