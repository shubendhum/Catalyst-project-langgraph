import uuid
from datetime import datetime
import pytest
from pydantic import BaseModel, EmailStr, ValidationError
from typing import Dict, Optional

# Define Pydantic models based on the specifications
class User(BaseModel):
    id: uuid.UUID
    email: EmailStr
    hashed_password: str
    is_active: bool = True
    created_at: datetime = None

    class Config:
        orm_mode = True


class DisplayHelloWorldMessage(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    data: Dict
    created_at: datetime = None
    updated_at: datetime = None

    class Config:
        orm_mode = True


class BackendAPIEndpoint(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    data: Dict
    created_at: datetime = None
    updated_at: datetime = None

    class Config:
        orm_mode = True


class FrontendIntegration(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    data: Dict
    created_at: datetime = None
    updated_at: datetime = None

    class Config:
        orm_mode = True


# Test cases
def test_user_validation():
    # Valid user
    user = User(
        id=uuid.uuid4(),
        email='test@example.com',
        hashed_password='hashed_password123',
    )
    assert user.is_active is True

    # Invalid email
    with pytest.raises(ValidationError):
        User(
            id=uuid.uuid4(),
            email='invalid_email',
            hashed_password='hashed_password123',
        )

    # Missing required field
    with pytest.raises(ValidationError):
        User(
            id=uuid.uuid4(),
            email='test@example.com',
        )


def test_display_hello_world_message_validation():
    user_id = uuid.uuid4()
    message = DisplayHelloWorldMessage(
        id=uuid.uuid4(),
        user_id=user_id,
        data={"message": "Hello, World!"},
    )
    assert message.data == {"message": "Hello, World!"}

    # Missing required field 'data'
    with pytest.raises(ValidationError):
        DisplayHelloWorldMessage(
            id=uuid.uuid4(),
            user_id=user_id,
        )


def test_backend_api_endpoint_validation():
    user_id = uuid.uuid4()
    endpoint = BackendAPIEndpoint(
        id=uuid.uuid4(),
        user_id=user_id,
        data={"api_endpoint": "/v1/resource"},
    )
    assert endpoint.data == {"api_endpoint": "/v1/resource"}

    # Missing required field 'data'
    with pytest.raises(ValidationError):
        BackendAPIEndpoint(
            id=uuid.uuid4(),
            user_id=user_id,
        )


def test_frontend_integration_validation():
    user_id = uuid.uuid4()
    integration = FrontendIntegration(
        id=uuid.uuid4(),
        user_id=user_id,
        data={"integration_source": "frontend"},
    )
    assert integration.data == {"integration_source": "frontend"}

    # Missing required field 'data'
    with pytest.raises(ValidationError):
        FrontendIntegration(
            id=uuid.uuid4(),
            user_id=user_id,
        )


def test_serialization_deserialization():
    user_id = uuid.uuid4()
    user = User(
        id=user_id,
        email='test@example.com',
        hashed_password='hashed_password123',
    )
    
    serialized_user = user.json()
    deserialized_user = User.parse_raw(serialized_user)
    assert user == deserialized_user


def test_relationships():
    user_id = uuid.uuid4()
    user = User(
        id=user_id,
        email='test@example.com',
        hashed_password='hashed_password123',
    )
    
    message = DisplayHelloWorldMessage(
        id=uuid.uuid4(),
        user_id=user.id,
        data={"message": "Hello, World!"},
    )
    
    assert message.user_id == user.id


def test_edge_cases():
    # Check for UUID validation
    with pytest.raises(ValidationError):
        User(
            id="invalid-uuid",
            email='test@example.com',
            hashed_password='hashed_password123',
        )

    # Check for empty data field
    with pytest.raises(ValidationError):
        DisplayHelloWorldMessage(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            data=None,
        )