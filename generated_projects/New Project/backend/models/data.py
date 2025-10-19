from datetime import datetime
from pydantic import BaseModel, Field, constr
from pydantic.networks import EmailStr
import uuid
from typing import Optional

class Greeting(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, alias="_id")
    message: constr(min_length=1)  # Required string with at least 1 character
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        # Enable aliasing to work with MongoDB "_id"
        allow_population_by_field_name = True
        json_encoders = {
            uuid.UUID: str  # Convert UUIDs to string in JSON representation
        }

# Example of how to instantiate the model
if __name__ == "__main__":
    greeting = Greeting(message="Hello, World!")
    print(greeting.json())