from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime

class User(BaseModel):
    id: UUID = Field(default_factory=uuid4, alias="_id")  # MongoDB uses `_id` as default ID field
    email: EmailStr
    hashed_password: str
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        orm_mode = True  # Enable ORM mode to work with different database libraries
        allow_population_by_field_name = True  # Allow population of models using field names defined in Pydantic
        json_encoders = {
            UUID: str  # Convert UUIDs to strings for JSON serialization
        }

    # Validation can also be added for specific cases, e.g., unique email checks, if integrated with a database

# Example usage
if __name__ == "__main__":
    user = User(email="test@example.com", hashed_password="hashed_password_value")
    print(user.json())