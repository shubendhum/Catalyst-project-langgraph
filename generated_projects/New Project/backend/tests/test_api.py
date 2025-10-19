import pytest
from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from fastapi.testclient import TestClient
from httpx import AsyncClient
from pydantic import BaseModel
from unittest.mock import MagicMock

# Sample FastAPI App
app = FastAPI()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class GreetRequest(BaseModel):
    name: str


class GreetResponse(BaseModel):
    message: str


@app.post("/api/greet", response_model=GreetResponse)
async def greet_user(payload: GreetRequest, token: str = Depends(oauth2_scheme)):
    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized")

    if not payload.name:
        raise HTTPException(status_code=400, detail="Bad Request")

    return GreetResponse(message=f"Hello, {payload.name}!")


@app.get("/api/greet", response_model=GreetResponse)
async def get_default_greeting(token: str = Depends(oauth2_scheme)):
    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized")

    return GreetResponse(message="Hello, World!")


# Test setup
@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def async_client():
    yield AsyncClient(app=app, base_url="http://test")


@pytest.fixture
def auth_token():
    return "Bearer testtoken"


@pytest.mark.asyncio
async def test_greet_user(client: TestClient, auth_token: str):
    response = await client.post("/api/greet", json={"name": "Alice"}, headers={"Authorization": auth_token})
    assert response.status_code == 200
    assert response.json() == {"message": "Hello, Alice!"}


@pytest.mark.asyncio
async def test_greet_user_bad_request(client: TestClient, auth_token: str):
    response = await client.post("/api/greet", json={}, headers={"Authorization": auth_token})
    assert response.status_code == 400
    assert response.json() == {"detail": "Bad Request"}


@pytest.mark.asyncio
async def test_greet_user_unauthorized(client: TestClient):
    response = await client.post("/api/greet", json={"name": "Alice"})
    assert response.status_code == 401
    assert response.json() == {"detail": "Unauthorized"}


@pytest.mark.asyncio
async def test_get_default_greeting(client: TestClient, auth_token: str):
    response = await client.get("/api/greet", headers={"Authorization": auth_token})
    assert response.status_code == 200
    assert response.json() == {"message": "Hello, World!"}


@pytest.mark.asyncio
async def test_get_default_greeting_unauthorized(client: TestClient):
    response = await client.get("/api/greet")
    assert response.status_code == 401
    assert response.json() == {"detail": "Unauthorized"}


@pytest.mark.asyncio
async def test_internal_server_error(client: TestClient, auth_token: str):
    # Simulate a server error situation
    async def error_greet_user(payload: GreetRequest):
        raise Exception("Internal Server Error")

    # Use a mock object to replace the actual function
    with pytest.raises(HTTPException):
        response = await client.post("/api/greet", json={"name": "Alice"}, headers={"Authorization": auth_token})


# To run the test with pytest, execute this command in the terminal:
# pytest -v -s