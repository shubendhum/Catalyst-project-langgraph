from pydantic import BaseModel, Field, conjoin
from typing import Dict, Optional
import uuid
from datetime import datetime

class GreetingMessage(BaseModel):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, alias="_id")
    user_id: Optional[uuid.UUID] = Field(default=None, title="User ID")
    data: Dict[str, any] = Field(..., title="Greeting Data")  # required field
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        # Allow for the alias `_id` (MongoDB convention for primary key)
        allow_population_by_field_name = True  
        json_encoders = {
            uuid.UUID: lambda v: str(v),  # Handle UUID serialization
            datetime: lambda v: v.isoformat()  # Handle datetime serialization
        }