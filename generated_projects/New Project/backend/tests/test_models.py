import pytest
from pydantic import BaseModel, ValidationError, Field
from bson import ObjectId
from datetime import datetime
from typing import Optional

# Define the Pydantic model for Message
class Message(BaseModel):
    id: ObjectId
    content: str = Field(..., description="Required field")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Auto-generated field")

# Helper function for creating a new ObjectId
def new_object_id():
    return ObjectId()

# Test cases for the Message model
class TestMessageModel:

    def test_valid_message_creation(self):
        message = Message(id=new_object_id(), content="Hello, World!")
        assert message.id is not None
        assert message.content == "Hello, World!"
        assert isinstance(message.timestamp, datetime)

    def test_missing_content(self):
        with pytest.raises(ValidationError) as exc:
            Message(id=new_object_id())
        assert "content" in str(exc.value)

    def test_empty_content(self):
        with pytest.raises(ValidationError) as exc:
            Message(id=new_object_id(), content="")
        assert "value is not a valid string" in str(exc.value)

    def test_timestamp_auto_generation(self):
        message = Message(id=new_object_id(), content="Testing auto timestamp")
        assert isinstance(message.timestamp, datetime)

    def test_id_is_objectid(self):
        with pytest.raises(ValidationError):
            Message(id="not-an-objectid", content="Invalid ID")

    def test_message_serialization(self):
        message = Message(id=new_object_id(), content="Serializable Message")
        serialized = message.json()
        deserialized = Message.parse_raw(serialized)
        assert deserialized.content == message.content
        assert deserialized.timestamp == message.timestamp
        assert deserialized.id == message.id

    def test_edge_case_empty_content(self):
        with pytest.raises(ValidationError):
            Message(id=new_object_id(), content=null)

    def test_edge_case_large_content(self):
        large_content = "A" * 10000  # Large content to test the limit
        message = Message(id=new_object_id(), content=large_content)
        assert message.content == large_content

    def test_invalid_id_type(self):
        with pytest.raises(ValidationError):
            Message(id=1234, content="This should fail")

    def test_id_field_required(self):
        with pytest.raises(ValidationError) as exc:
            Message(content="Message without ID")
        assert "field required" in str(exc.value)