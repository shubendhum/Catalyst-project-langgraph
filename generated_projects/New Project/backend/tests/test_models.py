import pytest
from uuid import uuid4
from datetime import datetime
from pydantic import BaseModel, EmailStr, ValidationError

# Define the Pydantic models based on the provided specs

class User(BaseModel):
    id: str  # should be a UUID
    email: EmailStr
    hashed_password: str
    is_active: bool = True
    created_at: datetime = None

    class Config:
        orm_mode = True

class IncrementCounter(BaseModel):
    id: str  # should be a UUID
    user_id: str  # should be a UUID referring to User
    data: dict
    created_at: datetime = None
    updated_at: datetime = None

    class Config:
        orm_mode = True

class DecrementCounter(BaseModel):
    id: str  # should be a UUID
    user_id: str  # should be a UUID referring to User
    data: dict
    created_at: datetime = None
    updated_at: datetime = None

    class Config:
        orm_mode = True

class ResetCounter(BaseModel):
    id: str  # should be a UUID
    user_id: str  # should be a UUID referring to User
    data: dict
    created_at: datetime = None
    updated_at: datetime = None

    class Config:
        orm_mode = True

# Test file

def test_user_model_validation():
    user_id = str(uuid4())
    
    # Valid case
    user = User(
        id=user_id,
        email="test@example.com",
        hashed_password="hashedpassword123",
        created_at=datetime.utcnow()
    )
    assert user.id == user_id
    assert user.email == "test@example.com"
    assert user.is_active is True

    # Invalid cases
    with pytest.raises(ValidationError):
        User(
            id=user_id,
            email="invalid-email",
            hashed_password="hashedpassword123"
        )
    with pytest.raises(ValidationError):
        User(
            id=user_id,
            email="test@example.com",
            hashed_password=None
        )

def test_increment_counter_model_validation():
    increment_counter_id = str(uuid4())
    user_id = str(uuid4())
    
    # Valid case
    increment_counter = IncrementCounter(
        id=increment_counter_id,
        user_id=user_id,
        data={"key": "value"},
        created_at=datetime.utcnow()
    )
    assert increment_counter.id == increment_counter_id
    assert increment_counter.data == {"key": "value"}

    # Invalid cases
    with pytest.raises(ValidationError):
        IncrementCounter(
            id=increment_counter_id,
            user_id=user_id,
            data=None
        )

def test_decrement_counter_model_validation():
    decrement_counter_id = str(uuid4())
    user_id = str(uuid4())
    
    # Valid case
    decrement_counter = DecrementCounter(
        id=decrement_counter_id,
        user_id=user_id,
        data={"key": "value"},
        created_at=datetime.utcnow()
    )
    assert decrement_counter.id == decrement_counter_id
    assert decrement_counter.data == {"key": "value"}

    # Invalid cases
    with pytest.raises(ValidationError):
        DecrementCounter(
            id=decrement_counter_id,
            user_id=user_id,
            data=None
        )

def test_reset_counter_model_validation():
    reset_counter_id = str(uuid4())
    user_id = str(uuid4())
    
    # Valid case
    reset_counter = ResetCounter(
        id=reset_counter_id,
        user_id=user_id,
        data={"key": "value"},
        created_at=datetime.utcnow()
    )
    assert reset_counter.id == reset_counter_id
    assert reset_counter.data == {"key": "value"}

    # Invalid cases
    with pytest.raises(ValidationError):
        ResetCounter(
            id=reset_counter_id,
            user_id=user_id,
            data=None
        )

def test_user_serialization():
    user_id = str(uuid4())
    user = User(
        id=user_id,
        email="test@example.com",
        hashed_password="hashedpassword123",
        created_at=datetime.utcnow()
    )
    
    user_json = user.json()
    assert "id" in user_json
    assert "email" in user_json
    assert "hashed_password" in user_json
    assert user_json['is_active'] is True
    assert user_json['created_at'] is not None

def test_relationships():
    user_id = str(uuid4())
    user = User(
        id=user_id,
        email="test@example.com",
        hashed_password="hashedpassword123",
    )
    
    increment_counter = IncrementCounter(
        id=str(uuid4()),
        user_id=user.id,
        data={"count": 1}
    )
    assert increment_counter.user_id == user.id

    decrement_counter = DecrementCounter(
        id=str(uuid4()),
        user_id=user.id,
        data={"count": 2}
    )
    assert decrement_counter.user_id == user.id

    reset_counter = ResetCounter(
        id=str(uuid4()),
        user_id=user.id,
        data={"reset": True}
    )
    assert reset_counter.user_id == user.id

# Edge cases tests
def test_user_model_empty_email():
    with pytest.raises(ValidationError):
        User(
            id=str(uuid4()),
            email="",
            hashed_password="hashedpassword123"
        )

def test_increment_counter_with_empty_data():
    with pytest.raises(ValidationError):
        IncrementCounter(
            id=str(uuid4()),
            user_id=str(uuid4()),
            data=None
        )

# Add more edge cases as necessary...

if __name__ == "__main__":
    pytest.main()