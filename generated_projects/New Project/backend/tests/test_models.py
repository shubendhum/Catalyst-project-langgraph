import pytest
from pydantic import BaseModel, EmailStr, validator, conlist
from uuid import uuid4
from datetime import datetime
from typing import Dict, Optional

# Pydantic models based on your specification
class User(BaseModel):
    id: str
    email: EmailStr
    hashed_password: str
    is_active: bool = True
    created_at: datetime = datetime.utcnow()

    @validator('id', pre=True, always=True)
    def generate_uuid(cls, v):
        return str(uuid4()) if v is None else v


class PersonalizedGreeting(BaseModel):
    id: str
    user_id: str
    data: Dict
    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()

    @validator('id', pre=True, always=True)
    def generate_uuid(cls, v):
        return str(uuid4()) if v is None else v


class UserInputForm(BaseModel):
    id: str
    user_id: str
    data: Dict
    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()

    @validator('id', pre=True, always=True)
    def generate_uuid(cls, v):
        return str(uuid4()) if v is None else v


class DisplayGreeting(BaseModel):
    id: str
    user_id: str
    data: Dict
    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()

    @validator('id', pre=True, always=True)
    def generate_uuid(cls, v):
        return str(uuid4()) if v is None else v

# Test cases
def test_user_validation():
    user = User(id=str(uuid4()), email="test@example.com", hashed_password="hashed_password")
    assert user.email == "test@example.com"
    assert user.is_active is True
    assert isinstance(user.created_at, datetime)

def test_user_missing_email():
    with pytest.raises(ValueError) as exc:
        User(id=str(uuid4()), hashed_password="hashed_password")
    assert "field required" in str(exc.value)

def test_personalized_greeting_validation():
    greeting = PersonalizedGreeting(id=str(uuid4()), user_id=str(uuid4()), data={"message": "Hello!"})
    assert greeting.data == {"message": "Hello!"}
    assert isinstance(greeting.created_at, datetime)
    assert isinstance(greeting.updated_at, datetime)

def test_user_input_form_validation():
    form = UserInputForm(id=str(uuid4()), user_id=str(uuid4()), data={"input": "value"})
    assert form.data == {"input": "value"}

def test_display_greeting_validation():
    greeting = DisplayGreeting(id=str(uuid4()), user_id=str(uuid4()), data={"highlight": "text"})
    assert greeting.data == {"highlight": "text"}

def test_serialization_user():
    user = User(id=str(uuid4()), email="user@example.com", hashed_password="password123")
    user_dict = user.dict()
    assert user_dict['email'] == "user@example.com"

def test_deserialization_user():
    user_data = {"id": str(uuid4()), "email": "user@example.com", "hashed_password": "hashedPassword"}
    user = User(**user_data)
    assert user.email == "user@example.com"

def test_edge_case_empty_email():
    with pytest.raises(ValueError):
        User(id=str(uuid4()), email="", hashed_password="hashed_password")

def test_edge_case_invalid_email():
    with pytest.raises(ValueError):
        User(id=str(uuid4()), email="invalid-email", hashed_password="hashed_password")

def test_relationship_user_personalized_greeting():
    user = User(id=str(uuid4()), email="relational@example.com", hashed_password="password123")
    greeting = PersonalizedGreeting(id=str(uuid4()), user_id=user.id, data={"message": "Welcome!"})
    assert greeting.user_id == user.id

@pytest.mark.parametrize("input_data", [
    {"id": None, "user_id": str(uuid4()), "data": {"key": "value"}},
    {"id": str(uuid4()), "user_id": None, "data": {"key": "value"}},
    {"id": str(uuid4()), "user_id": str(uuid4()), "data": None}
])
def test_edge_cases_personalized_greeting(input_data):
    with pytest.raises(ValueError):
        PersonalizedGreeting(**input_data)

# Additional edge cases can be added based on more complex validation requirements

if __name__ == "__main__":
    pytest.main()