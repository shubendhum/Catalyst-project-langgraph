from pydantic import BaseModel, Field, condecimal
from datetime import datetime
from uuid import UUID
from typing import Dict, Any, Optional

class UserInputForm(BaseModel):
    id: UUID = Field(..., alias='_id')
    user_id: UUID
    data: Dict[str, Any]
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow)

    class Config:
        allow_population_by_field_name = True
        use_enum_values = True
        arbitrary_types_allowed = True
        json_encoders = {
            UUID: str
        }

# Example to confirm how the model is intended to be used
if __name__ == "__main__":
    example_data = {
        "id": UUID("f47ac10b-58cc-4372-a567-0e02b2c3d479"),
        "user_id": UUID("a6d4c142-3e8f-4d30-bb2f-bbdb0a990338"),
        "data": {"key1": "value1", "key2": "value2"}
    }
    form = UserInputForm(**example_data)
    print(form.json())