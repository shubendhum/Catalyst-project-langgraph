import pytest
from fastapi import FastAPI, HTTPException
from httpx import AsyncClient
from fastapi_users import FastAPIUsers, models

from your_fastapi_app import app  # Adjust the import to your app's structure
from your_fastapi_app.database import get_db  # Adjust according to your database setup
from unittest.mock import patch


@pytest.fixture
def anyio_backend():
    return 'asyncio'


@pytest.fixture(scope="module")
async def async_client():
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
def user_data():
    return {
        "username": "testuser",
        "password": "testpass",
        "email": "testuser@example.com"
    }


@pytest.fixture
async def token(async_client, user_data):
    # Register the user
    response = await async_client.post("/api/register", json=user_data)
    response_data = response.json()
    yield response_data["token"]  # Assuming the token is sent back upon registration


@pytest.fixture
async def authenticated_client(async_client, token):
    async_client.headers = {
        "Authorization": f"Bearer {token}"
    }
    return async_client


@pytest.mark.asyncio
async def test_register(async_client, user_data):
    response = await async_client.post("/api/register", json=user_data)
    assert response.status_code == 200
    assert "message" in response.json()
    assert "user_id" in response.json()


@pytest.mark.asyncio
async def test_login(async_client, user_data):
    # First, register the user
    await async_client.post("/api/register", json=user_data)

    # Now, log the user in
    response = await async_client.post("/api/login", json={
        "username": user_data["username"],
        "password": user_data["password"]
    })
    assert response.status_code == 200
    assert "token" in response.json()
    assert "user_id" in response.json()


@pytest.mark.asyncio
async def test_get_counter(authenticated_client):
    response = await authenticated_client.get("/api/counter")
    assert response.status_code == 200
    assert "current_value" in response.json()
    assert "history_log" in response.json()


@pytest.mark.asyncio
async def test_increment_counter(authenticated_client):
    response = await authenticated_client.post("/api/counter/increment")
    assert response.status_code == 200
    assert "current_value" in response.json()


@pytest.mark.asyncio
async def test_decrement_counter(authenticated_client):
    response = await authenticated_client.post("/api/counter/decrement")
    assert response.status_code == 200
    assert "current_value" in response.json()


@pytest.mark.asyncio
async def test_reset_counter(authenticated_client):
    response = await authenticated_client.post("/api/counter/reset")
    assert response.status_code == 200
    assert "current_value" in response.json()


@pytest.mark.asyncio
async def test_register_user_bad_request(async_client):
    response = await async_client.post("/api/register", json={"username": "", "password": "", "email": ""})
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_login_user_bad_request(async_client):
    response = await async_client.post("/api/login", json={"username": "fakeuser", "password": "wrongpass"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_counter_unauthorized(async_client):
    response = await async_client.get("/api/counter")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_increment_counter_unauthorized(async_client):
    response = await async_client.post("/api/counter/increment")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_server_error(async_client):
    # Mocking to simulate a server error e.g. database not available
    with patch("your_fastapi_app.database.get_db", side_effect=Exception("Database error")):
        response = await async_client.get("/api/counter")
        assert response.status_code == 500


# Additional tests can be included as necessary, following the pattern above.