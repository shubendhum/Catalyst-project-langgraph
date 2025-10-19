from pydantic import BaseModel, Field, condec, validator
from uuid import UUID
from datetime import datetime
from typing import Dict, Optional

class PersonalizedGreeting(BaseModel):
    id: UUID = Field(default_factory=UUID, alias="_id")
    user_id: UUID
    data: Dict[str, condec.any]  # Assuming the dict can have any type of value; adjust as needed
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        allow_population_by_field_name = True  # Allows usage of "id" instead of "_id" for population
        json_encoders = {
            UUID: str,  # Encode UUID as string in JSON
            datetime: lambda v: v.isoformat()  # ISO format for datetime
        }
        anystr_strip_whitespace = True  # Strips whitespace from any strings
        validate_assignment = True  # Validate on assignment

    # Optional: Define any additional validators here.
    @validator('user_id', pre=True)
    def validate_user_id(cls, v):
        if v is None:
            raise ValueError('user_id must be provided')
        return v

    # Optional: Additional validation can be added similarly for other fields if needed.

# Example usage:
# greeting = PersonalizedGreeting(
#     user_id=UUID("12345678-1234-5678-1234-567812345678"),
#     data={"message": "Hello, World!"}
# )
# print(greeting.json())