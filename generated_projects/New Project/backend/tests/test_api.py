import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI, HTTPException, status
from httpx import AsyncClient
from pydantic import BaseModel

# Assuming you have a main.py or app.py file with your FastAPI application
from app import app  # Import your FastAPI app

# Mock models - adjust according to your actual models
class TodoModel(BaseModel):
    id: str
    title: str
    description: str
    completed: bool
    priority: str
    created_at: datetime
    updated_at: datetime
    due_date: Optional[datetime] = None


# Test data
TEST_USER_ID = "test-user-123"
MOCK_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0LXVzZXItMTIzIiwiZXhwIjoxNjAwMDAwMDAwfQ.signature"
MOCK_TODO_ID = "todo-123"

MOCK_TODO = {
    "id": MOCK_TODO_ID,
    "title": "Test Todo",
    "description": "This is a test todo item",
    "completed": False,
    "priority": "high",
    "created_at": datetime.now().isoformat(),
    "updated_at": datetime.now().isoformat(),
    "due_date": (datetime.now() + timedelta(days=1)).isoformat()
}

MOCK_TODOS = [
    MOCK_TODO,
    {
        "id": "todo-456",
        "title": "Another Todo",
        "description": "This is another test todo item",
        "completed": True,
        "priority": "medium",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "due_date": None
    }
]


# Fixtures
@pytest.fixture
def auth_headers():
    """Fixture to provide authentication headers"""
    return {"Authorization": f"Bearer {MOCK_TOKEN}"}


@pytest.fixture
async def async_client():
    """Fixture for creating async HTTP client"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


# Mock the authentication dependency
@pytest.fixture(autouse=True)
def mock_auth_dependency():
    """Mock the authentication dependency to always return the test user ID"""
    with patch("app.dependencies.get_current_user", return_value=TEST_USER_ID):
        yield


# Mock database operations
@pytest.fixture(autouse=True)
def mock_db_operations():
    """Mock database operations to avoid actual database calls"""
    with patch("app.repositories.todo_repository.TodoRepository") as mock_repo:
        mock_instance = mock_repo.return_value
        
        # Mock get_all method
        mock_instance.get_all = AsyncMock(return_value=MOCK_TODOS)
        
        # Mock get_by_id method
        async def mock_get_by_id(todo_id):
            if todo_id == MOCK_TODO_ID:
                return MOCK_TODO
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")
        
        mock_instance.get_by_id = AsyncMock(side_effect=mock_get_by_id)
        
        # Mock create method
        mock_instance.create = AsyncMock(return_value=MOCK_TODO)
        
        # Mock update method
        mock_instance.update = AsyncMock(return_value=MOCK_TODO)
        
        # Mock delete method
        mock_instance.delete = AsyncMock(return_value=None)
        
        # Mock filtered query
        mock_instance.get_filtered = AsyncMock(return_value=MOCK_TODOS)
        
        yield mock_instance


# Tests for GET /api/todos
@pytest.mark.asyncio
async def test_get_all_todos(async_client, auth_headers):
    """Test getting all todos"""
    response = await async_client.get("/api/todos", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) == 2
    assert data["items"][0]["id"] == MOCK_TODO_ID


@pytest.mark.asyncio
async def test_get_filtered_todos_by_completed(async_client, auth_headers, mock_db_operations):
    """Test getting todos filtered by completed status"""
    mock_db_operations.get_filtered = AsyncMock(return_value=[MOCK_TODOS[1]])
    
    response = await async_client.get("/api/todos?completed=true", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) == 1
    assert data["items"][0]["completed"] is True


@pytest.mark.asyncio
async def test_get_filtered_todos_by_priority(async_client, auth_headers, mock_db_operations):
    """Test getting todos filtered by priority"""
    mock_db_operations.get_filtered = AsyncMock(return_value=[MOCK_TODOS[0]])
    
    response = await async_client.get("/api/todos?priority=high", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert len(data["items"]) == 1
    assert data["items"][0]["priority"] == "high"


@pytest.mark.asyncio
async def test_get_todos_unauthorized(async_client):
    """Test getting todos without authentication"""
    # Override the mock_auth_dependency for this test
    with patch("app.dependencies.get_current_user", side_effect=HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid authentication credentials")):
        response = await async_client.get("/api/todos")
        assert response.status_code == 401


# Tests for GET /api/todos/{todo_id}
@pytest.mark.asyncio
async def test_get_todo_by_id(async_client, auth_headers):
    """Test getting a specific todo by ID"""
    response = await async_client.get(f"/api/todos/{MOCK_TODO_ID}", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == MOCK_TODO_ID
    assert data["title"] == "Test Todo"


@pytest.mark.asyncio
async def test_get_todo_not_found(async_client, auth_headers):
    """Test getting a non-existent todo"""
    response = await async_client.get("/api/todos/non-existent-id", headers=auth_headers)
    
    assert response.status_code == 404
    assert "Todo not found" in response.json()["detail"]


# Tests for POST /api/todos
@pytest.mark.asyncio
async def test_create_todo(async_client, auth_headers):
    """Test creating a new todo"""
    new_todo = {
        "title": "New Todo",
        "description": "This is a new todo item",
        "priority": "low",
        "due_date": (datetime.now() + timedelta(days=2)).isoformat()
    }
    
    response = await async_client.post("/api/todos", json=new_todo, headers=auth_headers)
    
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Todo"  # Using mock data which returns MOCK_TODO


@pytest.mark.asyncio
async def test_create_todo_missing_required_fields(async_client, auth_headers):
    """Test creating a todo with missing required fields"""
    new_todo = {
        "description": "Missing title field"
    }
    
    response = await async_client.post("/api/todos", json=new_todo, headers=auth_headers)
    
    assert response.status_code == 422  # Validation error


# Tests for PUT /api/todos/{todo_id}
@pytest.mark.asyncio
async def test_update_todo(async_client, auth_headers):
    """Test updating a todo"""
    update_data = {
        "title": "Updated Todo",
        "completed": True
    }
    
    response = await async_client.put(f"/api/todos/{MOCK_TODO_ID}", json=update_data, headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    # Our mock returns the original MOCK_TODO, but in a real app it would be updated
    assert data["id"] == MOCK_TODO_ID


@pytest.mark.asyncio
async def test_update_todo_not_found(async_client, auth_headers, mock_db_operations):
    """Test updating a non-existent todo"""
    mock_db_operations.update = AsyncMock(side_effect=HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found"))
    
    update_data = {
        "title": "Updated Todo",
        "completed": True
    }
    
    response = await async_client.put("/api/todos/non-existent-id", json=update_data, headers=auth_headers)
    
    assert response.status_code == 404
    assert "Todo not found" in response.json()["detail"]


# Tests for DELETE /api/todos/{todo_id}
@pytest.mark.asyncio
async def test_delete_todo(async_client, auth_headers):
    """Test deleting a todo"""
    response = await async_client.delete(f"/api/todos/{MOCK_TODO_ID}", headers=auth_headers)
    
    assert response.status_code == 204
    assert response.text == ""  # No content


@pytest.mark.asyncio
async def test_delete_todo_not_found(async_client, auth_headers, mock_db_operations):
    """Test deleting a non-existent todo"""
    mock_db_operations.delete = AsyncMock(side_effect=HTTPException(
        status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found"))
    
    response = await async_client.delete("/api/todos/non-existent-id", headers=auth_headers)
    
    assert response.status_code == 404
    assert "Todo not found" in response.json()["detail"]


# Tests for PATCH /api/todos/{todo_id}/complete
@pytest.mark.asyncio
async def test_toggle_todo_completion(async_client, auth_headers):
    """Test toggling a todo's completion status"""
    response = await async_client.patch(f"/api/todos/{MOCK_TODO_ID}/complete", headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == MOCK_TODO_ID


@pytest.mark.asyncio
async def test_toggle_completion_not_found(async_client, auth_headers, mock_db_operations):
    """Test toggling completion of a non-existent todo"""
    # Mock the specific method used for toggling completion
    with patch("app.services.todo_service.TodoService.toggle_completion", 
               side_effect=HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found")):
        
        response = await async_client.patch("/api/todos/non-existent-id/complete", headers=auth_headers)
        
        assert response.status_code == 404
        assert "Todo not found" in response.json()["detail"]


# Server error tests
@pytest.mark.asyncio
async def test_server_error(async_client, auth_headers, mock_db_operations):
    """Test server error handling"""
    mock_db_operations.get_all = AsyncMock(side_effect=Exception("Unexpected database error"))
    
    response = await async_client.get("/api/todos", headers=auth_headers)
    
    assert response.status_code == 500
    assert "Internal server error" in response.json()["detail"]