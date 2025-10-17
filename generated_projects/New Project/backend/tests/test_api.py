import pytest
import json
from datetime import datetime
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient
from fastapi import FastAPI
from typing import List, Dict, Any

# Assuming your main app is in main.py
from main import app
from models import GreetingResponse, GreetingCreate  # Import your models here


# ----- FIXTURES ----- #

@pytest.fixture
def test_app():
    """Return the FastAPI application for testing."""
    return app


@pytest.fixture
def mock_db_session():
    """Mock database session."""
    mock = MagicMock()
    # Setup the mock to return specific values for different method calls
    return mock


@pytest.fixture
async def async_client(test_app: FastAPI):
    """Create an async HTTP client for testing the API."""
    async with AsyncClient(app=test_app, base_url="http://test") as client:
        yield client


@pytest.fixture
def mock_greeting_db_entry():
    """Sample greeting database entry."""
    return {
        "id": "1",
        "name": "John",
        "message": "Hello, John!",
        "timestamp": datetime.now().isoformat()
    }


@pytest.fixture
def mock_greeting_list():
    """Sample list of greeting database entries."""
    return [
        {
            "id": "1",
            "name": "John",
            "message": "Hello, John!",
            "timestamp": datetime.now().isoformat()
        },
        {
            "id": "2",
            "name": "Jane",
            "message": "Hello, Jane!",
            "timestamp": datetime.now().isoformat()
        }
    ]


# ----- TESTS ----- #

# Test GET /api/greeting
@pytest.mark.asyncio
async def test_get_default_greeting(async_client: AsyncClient):
    """Test getting the default greeting."""
    response = await async_client.get("/api/greeting")
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    
    data = response.json()
    assert "message" in data
    assert data["message"] == "Hello, World!"


# Test error handling for GET /api/greeting
@pytest.mark.asyncio
@patch("routes.greeting.get_default_greeting", side_effect=Exception("Test exception"))
async def test_get_default_greeting_server_error(mock_get, async_client: AsyncClient):
    """Test server error handling for default greeting endpoint."""
    response = await async_client.get("/api/greeting")
    
    assert response.status_code == 500
    assert response.json()["detail"] == "Internal server error"


# Test GET /api/greeting/{name}
@pytest.mark.asyncio
async def test_get_personalized_greeting(async_client: AsyncClient):
    """Test getting a personalized greeting."""
    name = "John"
    response = await async_client.get(f"/api/greeting/{name}")
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    
    data = response.json()
    assert "message" in data
    assert data["message"] == f"Hello, {name}!"


# Test validation error for GET /api/greeting/{name}
@pytest.mark.asyncio
async def test_get_personalized_greeting_validation_error(async_client: AsyncClient):
    """Test validation error handling for personalized greeting endpoint."""
    # Assuming validation error occurs with empty name
    response = await async_client.get("/api/greeting/")
    
    assert response.status_code == 422
    assert "detail" in response.json()


# Test error handling for GET /api/greeting/{name}
@pytest.mark.asyncio
@patch("routes.greeting.get_personalized_greeting", side_effect=Exception("Test exception"))
async def test_get_personalized_greeting_server_error(mock_get, async_client: AsyncClient):
    """Test server error handling for personalized greeting endpoint."""
    response = await async_client.get("/api/greeting/John")
    
    assert response.status_code == 500
    assert response.json()["detail"] == "Internal server error"


# Test POST /api/greeting
@pytest.mark.asyncio
@patch("routes.greeting.save_greeting")
async def test_create_greeting(mock_save_greeting, async_client: AsyncClient, mock_greeting_db_entry):
    """Test creating a new greeting."""
    mock_save_greeting.return_value = mock_greeting_db_entry
    
    # Prepare request payload
    payload = {"name": "John"}
    
    # Send request
    response = await async_client.post(
        "/api/greeting",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    # Assert response
    assert response.status_code == 201
    assert response.headers["content-type"] == "application/json"
    
    # Verify response data
    data = response.json()
    assert "id" in data
    assert "name" in data
    assert "message" in data
    assert "timestamp" in data
    assert data["name"] == "John"
    
    # Verify the mock was called correctly
    mock_save_greeting.assert_called_once_with(payload["name"])


# Test validation error for POST /api/greeting
@pytest.mark.asyncio
async def test_create_greeting_validation_error(async_client: AsyncClient):
    """Test validation error handling for create greeting endpoint."""
    # Empty payload should cause validation error
    response = await async_client.post(
        "/api/greeting",
        json={},
        headers={"Content-Type": "application/json"}
    )
    
    assert response.status_code == 422
    assert "detail" in response.json()


# Test error handling for POST /api/greeting
@pytest.mark.asyncio
@patch("routes.greeting.save_greeting", side_effect=Exception("Test exception"))
async def test_create_greeting_server_error(mock_save_greeting, async_client: AsyncClient):
    """Test server error handling for create greeting endpoint."""
    payload = {"name": "John"}
    
    response = await async_client.post(
        "/api/greeting",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    assert response.status_code == 500
    assert response.json()["detail"] == "Internal server error"


# Test GET /api/greetings
@pytest.mark.asyncio
@patch("routes.greeting.get_all_greetings")
async def test_get_greetings_history(mock_get_all_greetings, async_client: AsyncClient, mock_greeting_list):
    """Test getting the history of saved greetings."""
    mock_get_all_greetings.return_value = mock_greeting_list
    
    response = await async_client.get("/api/greetings")
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    
    data = response.json()
    assert "greetings" in data
    assert isinstance(data["greetings"], list)
    assert len(data["greetings"]) == 2
    
    # Verify structure of each greeting
    for greeting in data["greetings"]:
        assert "id" in greeting
        assert "name" in greeting
        assert "message" in greeting
        assert "timestamp" in greeting
    
    # Verify the mock was called
    mock_get_all_greetings.assert_called_once()


# Test error handling for GET /api/greetings
@pytest.mark.asyncio
@patch("routes.greeting.get_all_greetings", side_effect=Exception("Test exception"))
async def test_get_greetings_history_server_error(mock_get_all_greetings, async_client: AsyncClient):
    """Test server error handling for greeting history endpoint."""
    response = await async_client.get("/api/greetings")
    
    assert response.status_code == 500
    assert response.json()["detail"] == "Internal server error"


# ----- DATABASE MOCK TESTS ----- #

@pytest.mark.asyncio
@patch("db.greeting_repository.GreetingRepository.save_greeting")
async def test_db_save_greeting(mock_save_greeting, async_client: AsyncClient, mock_greeting_db_entry):
    """Test that the database repository is called correctly when saving a greeting."""
    mock_save_greeting.return_value = mock_greeting_db_entry
    
    # Prepare request payload
    payload = {"name": "John"}
    
    # Send request
    await async_client.post(
        "/api/greeting",
        json=payload,
        headers={"Content-Type": "application/json"}
    )
    
    # Verify repository method was called with correct parameters
    # Adjust this according to your actual implementation
    expected_greeting_create = GreetingCreate(name="John")
    mock_save_greeting.assert_called_once()  # Add parameter check if needed


@pytest.mark.asyncio
@patch("db.greeting_repository.GreetingRepository.get_all_greetings")
async def test_db_get_all_greetings(mock_get_all_greetings, async_client: AsyncClient, mock_greeting_list):
    """Test that the database repository is called correctly when getting all greetings."""
    mock_get_all_greetings.return_value = mock_greeting_list
    
    # Send request
    await async_client.get("/api/greetings")
    
    # Verify repository method was called
    mock_get_all_greetings.assert_called_once()