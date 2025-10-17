import pytest
from datetime import datetime
from bson import ObjectId
from pydantic import ValidationError
import pytz

# Import your models - adjust import path as needed
from models import Greeting

class TestGreetingModel:
    """Tests for the Greeting Pydantic model."""
    
    def test_valid_greeting(self):
        """Test creating a valid Greeting object."""
        now = datetime.now(pytz.UTC)
        greeting = Greeting(
            _id=ObjectId(),
            name="John Doe",
            message="Hello, John Doe!",
            timestamp=now
        )
        
        assert isinstance(greeting._id, ObjectId)
        assert greeting.name == "John Doe"
        assert greeting.message == "Hello, John Doe!"
        assert greeting.timestamp == now
    
    def test_default_timestamp(self):
        """Test that timestamp defaults to current time if not provided."""
        before = datetime.now(pytz.UTC)
        greeting = Greeting(
            _id=ObjectId(),
            name="John Doe",
            message="Hello, John Doe!"
        )
        after = datetime.now(pytz.UTC)
        
        assert greeting.timestamp is not None
        assert before <= greeting.timestamp <= after
    
    def test_auto_generated_id(self):
        """Test that _id is auto-generated if not provided."""
        greeting = Greeting(
            name="John Doe",
            message="Hello, John Doe!"
        )
        
        assert greeting._id is not None
        assert isinstance(greeting._id, ObjectId)
    
    def test_empty_name_validation(self):
        """Test that empty name raises ValidationError."""
        with pytest.raises(ValidationError):
            Greeting(
                name="",
                message="Hello!"
            )
    
    def test_missing_name_validation(self):
        """Test that missing name raises ValidationError."""
        with pytest.raises(ValidationError):
            Greeting(
                message="Hello!"
            )
    
    def test_empty_message_validation(self):
        """Test that empty message raises ValidationError."""
        with pytest.raises(ValidationError):
            Greeting(
                name="John Doe",
                message=""
            )
    
    def test_missing_message_validation(self):
        """Test that missing message raises ValidationError."""
        with pytest.raises(ValidationError):
            Greeting(
                name="John Doe"
            )
    
    def test_serialization(self):
        """Test serializing a Greeting object to dict/JSON."""
        obj_id = ObjectId()
        now = datetime.now(pytz.UTC)
        greeting = Greeting(
            _id=obj_id,
            name="John Doe",
            message="Hello, John Doe!",
            timestamp=now
        )
        
        serialized = greeting.dict()
        
        assert serialized["_id"] == obj_id
        assert serialized["name"] == "John Doe"
        assert serialized["message"] == "Hello, John Doe!"
        assert serialized["timestamp"] == now
    
    def test_deserialization(self):
        """Test deserializing JSON/dict to a Greeting object."""
        obj_id = ObjectId()
        now = datetime.now(pytz.UTC)
        data = {
            "_id": obj_id,
            "name": "John Doe",
            "message": "Hello, John Doe!",
            "timestamp": now
        }
        
        greeting = Greeting(**data)
        
        assert greeting._id == obj_id
        assert greeting.name == "John Doe"
        assert greeting.message == "Hello, John Doe!"
        assert greeting.timestamp == now
    
    def test_deserialization_with_string_id(self):
        """Test deserializing with string ObjectId."""
        obj_id = ObjectId()
        data = {
            "_id": str(obj_id),
            "name": "John Doe",
            "message": "Hello, John Doe!",
            "timestamp": datetime.now(pytz.UTC)
        }
        
        # This would pass only if your model handles string ObjectId conversion
        # If not, adjust this test accordingly
        with pytest.raises(ValidationError):
            greeting = Greeting(**data)
    
    def test_very_long_fields(self):
        """Test validation with extremely long field values."""
        long_string = "a" * 1000
        greeting = Greeting(
            name=long_string,
            message=long_string
        )
        
        assert greeting.name == long_string
        assert greeting.message == long_string
    
    def test_whitespace_only_fields(self):
        """Test that whitespace-only fields fail validation."""
        with pytest.raises(ValidationError):
            Greeting(
                name="   ",
                message="Hello!"
            )
        
        with pytest.raises(ValidationError):
            Greeting(
                name="John Doe",
                message="   "
            )