from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime

class User(BaseModel):
    id: UUID = Field(default_factory=uuid4, alias="_id")
    email: EmailStr = Field(..., unique=True)
    hashed_password: str = Field(...)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        allow_population_by_field_name = True
        use_enum_values = True

    # You can add additional methods or validators here if needed,
    # such as checking for password strength or other business rules.