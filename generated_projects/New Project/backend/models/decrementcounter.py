from pydantic import BaseModel, Field, constr
from typing import Dict, Optional
from uuid import UUID
from datetime import datetime

class DecrementCounter(BaseModel):
    id: UUID = Field(..., alias="_id")  # MongoDB uses _id for document IDs
    user_id: UUID = Field(..., description="The user associated with this decrement counter.")
    data: Dict[str, any] = Field(..., description="A dictionary containing decrement counter data.")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="The timestamp when the counter was created.")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="The timestamp when the counter was last updated.")

    class Config:
        # Allow arbitrary types in the dict field and use Pydantic models
        json_encoders = {
            UUID: str
        }
        allow_population_by_field_name = True  # Allows alias use when populating models
        orm_mode = True  # Enable ORM mode to work seamlessly with ORMs

# Example of how to use the model (not part of the model itself)
if __name__ == "__main__":
    example = DecrementCounter(
        id=UUID("123e4567-e89b-12d3-a456-426614174000"),
        user_id=UUID("123e4567-e89b-12d3-a456-426614174001"),
        data={"count": 10}
    )
    print(example.json())