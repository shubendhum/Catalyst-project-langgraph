import pytest
import uuid
from datetime import datetime, timezone
from pydantic import ValidationError
from typing import Dict, Any
import json

# Import your models here - adjust the import path as needed
from your_app.models import User, TaskCreation, TaskListing, TaskCompletion

class TestUserModel:
    def test_valid_user_creation(self):
        """Test creating a valid user"""
        user_id = uuid.uuid4()
        user = User(
            id=user_id,
            email="test@example.com",
            hashed_password="hashedpassword123"
        )
        assert user.id == user_id
        assert user.email == "test@example.com"
        assert user.hashed_password == "hashedpassword123"
        assert user.is_active is True  # default value
        assert isinstance(user.created_at, datetime)

    def test_missing_required_fields(self):
        """Test validation error when required fields are missing"""
        with pytest.raises(ValidationError) as exc_info:
            User(id=uuid.uuid4())
        
        errors = exc_info.value.errors()
        assert any(e["loc"][0] == "email" for e in errors)
        assert any(e["loc"][0] == "hashed_password" for e in errors)

    def test_invalid_email_format(self):
        """Test validation error for invalid email format"""
        with pytest.raises(ValidationError) as exc_info:
            User(
                id=uuid.uuid4(),
                email="invalid-email",
                hashed_password="hashedpassword123"
            )
        
        errors = exc_info.value.errors()
        assert any(e["loc"][0] == "email" for e in errors)

    def test_uuid_validation(self):
        """Test validation of UUID field"""
        with pytest.raises(ValidationError) as exc_info:
            User(
                id="not-a-uuid",
                email="test@example.com",
                hashed_password="hashedpassword123"
            )
        
        errors = exc_info.value.errors()
        assert any(e["loc"][0] == "id" for e in errors)

    def test_user_serialization(self):
        """Test user serialization to dict/JSON"""
        user_id = uuid.uuid4()
        user = User(
            id=user_id,
            email="test@example.com",
            hashed_password="hashedpassword123"
        )
        
        user_dict = user.model_dump()
        assert user_dict["id"] == user_id
        assert user_dict["email"] == "test@example.com"
        assert user_dict["hashed_password"] == "hashedpassword123"
        assert user_dict["is_active"] is True
        
        # Verify JSON serialization works
        user_json = user.model_dump_json()
        assert isinstance(user_json, str)
        user_from_json = json.loads(user_json)
        assert user_from_json["email"] == "test@example.com"

    def test_user_deserialization(self):
        """Test creating a user from dict"""
        user_id = uuid.uuid4()
        user_data = {
            "id": str(user_id),
            "email": "test@example.com",
            "hashed_password": "hashedpassword123",
            "is_active": False,
            "created_at": "2023-01-01T00:00:00Z"
        }
        
        user = User.model_validate(user_data)
        assert user.id == user_id
        assert user.email == "test@example.com"
        assert user.is_active is False
        assert user.created_at.year == 2023


class TestTaskCreationModel:
    def test_valid_task_creation(self):
        """Test creating a valid TaskCreation"""
        task_id = uuid.uuid4()
        user_id = uuid.uuid4()
        task_data: Dict[str, Any] = {"title": "Test Task", "description": "Test Description"}
        
        task = TaskCreation(
            id=task_id,
            user_id=user_id,
            data=task_data
        )
        
        assert task.id == task_id
        assert task.user_id == user_id
        assert task.data == task_data
        assert isinstance(task.created_at, datetime)
        assert isinstance(task.updated_at, datetime)

    def test_missing_required_fields(self):
        """Test validation error when required fields are missing"""
        with pytest.raises(ValidationError) as exc_info:
            TaskCreation(
                id=uuid.uuid4(),
                user_id=uuid.uuid4()
                # missing data field
            )
        
        errors = exc_info.value.errors()
        assert any(e["loc"][0] == "data" for e in errors)

    def test_invalid_data_type(self):
        """Test validation error when data is not a dict"""
        with pytest.raises(ValidationError) as exc_info:
            TaskCreation(
                id=uuid.uuid4(),
                user_id=uuid.uuid4(),
                data="not a dict"  # should be a dict
            )
        
        errors = exc_info.value.errors()
        assert any(e["loc"][0] == "data" for e in errors)

    def test_invalid_user_id(self):
        """Test validation error when user_id is not a valid UUID"""
        with pytest.raises(ValidationError) as exc_info:
            TaskCreation(
                id=uuid.uuid4(),
                user_id="not-a-uuid",
                data={"title": "Test"}
            )
        
        errors = exc_info.value.errors()
        assert any(e["loc"][0] == "user_id" for e in errors)

    def test_task_creation_serialization(self):
        """Test TaskCreation serialization to dict/JSON"""
        task_id = uuid.uuid4()
        user_id = uuid.uuid4()
        task_data = {"title": "Test Task", "description": "Test Description"}
        
        task = TaskCreation(
            id=task_id,
            user_id=user_id,
            data=task_data
        )
        
        task_dict = task.model_dump()
        assert task_dict["id"] == task_id
        assert task_dict["user_id"] == user_id
        assert task_dict["data"] == task_data
        
        # Verify JSON serialization works
        task_json = task.model_dump_json()
        assert isinstance(task_json, str)
        task_from_json = json.loads(task_json)
        assert task_from_json["data"]["title"] == "Test Task"


class TestTaskListingModel:
    def test_valid_task_listing(self):
        """Test creating a valid TaskListing"""
        task_id = uuid.uuid4()
        user_id = uuid.uuid4()
        task_data = {"title": "Test Listing", "status": "open"}
        
        task = TaskListing(
            id=task_id,
            user_id=user_id,
            data=task_data
        )
        
        assert task.id == task_id
        assert task.user_id == user_id
        assert task.data == task_data
        assert isinstance(task.created_at, datetime)
        assert isinstance(task.updated_at, datetime)

    def test_missing_required_fields(self):
        """Test validation error when required fields are missing"""
        with pytest.raises(ValidationError) as exc_info:
            TaskListing(
                id=uuid.uuid4(),
                user_id=uuid.uuid4()
                # missing data field
            )
        
        errors = exc_info.value.errors()
        assert any(e["loc"][0] == "data" for e in errors)

    def test_complex_data_structure(self):
        """Test TaskListing with complex nested data structure"""
        task_data = {
            "title": "Complex Task",
            "status": "open",
            "tags": ["important", "urgent"],
            "details": {
                "priority": 1,
                "steps": [
                    {"step": 1, "description": "First step"},
                    {"step": 2, "description": "Second step"}
                ]
            }
        }
        
        task = TaskListing(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            data=task_data
        )
        
        assert task.data["details"]["steps"][0]["description"] == "First step"
        
        # Test JSON serialization of complex data
        task_json = task.model_dump_json()
        task_from_json = json.loads(task_json)
        assert task_from_json["data"]["details"]["steps"][1]["step"] == 2


class TestTaskCompletionModel:
    def test_valid_task_completion(self):
        """Test creating a valid TaskCompletion"""
        task_id = uuid.uuid4()
        user_id = uuid.uuid4()
        completion_data = {"completion_date": "2023-05-15", "status": "completed"}
        
        completion = TaskCompletion(
            id=task_id,
            user_id=user_id,
            data=completion_data
        )
        
        assert completion.id == task_id
        assert completion.user_id == user_id
        assert completion.data == completion_data
        assert isinstance(completion.created_at, datetime)
        assert isinstance(completion.updated_at, datetime)

    def test_task_completion_relationship(self):
        """Test relationship between TaskCompletion and User via user_id"""
        # In a real test with a database, you would test the relationship by
        # creating a User and then a TaskCompletion with the User's ID, then
        # verify the relationship. Here we simulate that logic.
        
        user_id = uuid.uuid4()
        
        # First create a user
        user = User(
            id=user_id,
            email="test@example.com",
            hashed_password="hashedpassword123"
        )
        
        # Then create a task completion with the user's ID
        completion = TaskCompletion(
            id=uuid.uuid4(),
            user_id=user_id,
            data={"status": "completed"}
        )
        
        # Verify the user_id matches
        assert completion.user_id == user.id

    def test_data_field_flexibility(self):
        """Test that the data field can accept different structures"""
        # Simple data
        simple_data = {"status": "completed"}
        completion1 = TaskCompletion(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            data=simple_data
        )
        assert completion1.data == simple_data
        
        # Complex data
        complex_data = {
            "status": "completed",
            "metrics": {"time_spent": 120, "accuracy": 0.95},
            "feedback": ["Great job!", "Fast completion"],
            "reviewer": {"id": str(uuid.uuid4()), "name": "Reviewer"}
        }
        
        completion2 = TaskCompletion(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            data=complex_data
        )
        assert completion2.data == complex_data
        
        # Empty dict (should be valid as long as the field exists)
        empty_data = {}
        completion3 = TaskCompletion(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            data=empty_data
        )
        assert completion3.data == empty_data


class TestModelEdgeCases:
    def test_datetime_serialization(self):
        """Test datetime serialization to ensure it's in the correct format"""
        user = User(
            id=uuid.uuid4(),
            email="test@example.com",
            hashed_password="hashedpassword123",
            created_at=datetime(2023, 1, 1, tzinfo=timezone.utc)
        )
        
        user_dict = user.model_dump()
        assert isinstance(user_dict["created_at"], datetime)
        
        # Ensure ISO format works in JSON
        user_json = user.model_dump_json()
        user_from_json = json.loads(user_json)
        # The format might be slightly different depending on Pydantic version
        assert "2023-01-01" in user_from_json["created_at"]

    def test_extremely_large_data(self):
        """Test model with extremely large nested data structure"""
        # Create a deeply nested structure
        nested_data = {}
        current = nested_data
        for i in range(10):  # 10 levels deep
            current["level"] = i
            current["next"] = {}
            current = current["next"]
        
        task = TaskCreation(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            data=nested_data
        )
        
        # Check serialization/deserialization
        task_json = task.model_dump_json()
        task_from_json = json.loads(task_json)
        
        # Verify we can access deep elements
        current = task_from_json["data"]
        for i in range(10):
            assert current["level"] == i
            if i < 9:  # Last level doesn't have "next"
                current = current["next"]

    def test_empty_but_required_fields(self):
        """Test how models handle empty but required fields"""
        # Empty string for email should fail
        with pytest.raises(ValidationError) as exc_info:
            User(
                id=uuid.uuid4(),
                email="",  # Empty but required
                hashed_password="hashedpassword123"
            )
        
        errors = exc_info.value.errors()
        assert any(e["loc"][0] == "email" for e in errors)
        
        # Empty dict for data (required) should pass validation
        task = TaskCreation(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            data={}  # Empty but required
        )
        assert task.data == {}