from uuid import UUID, uuid4
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional

class User(BaseModel):
    id: UUID = Field(default_factory=uuid4, title="User ID")
    email: EmailStr = Field(..., unique=True, title="User Email")
    hashed_password: str = Field(..., title="Hashed Password")
    is_active: bool = Field(default=True, title="Is Active")
    created_at: datetime = Field(default_factory=datetime.utcnow, title="Creation Timestamp")

    class Config:
        # Ensure that Pydantic uses the json-compatible schema
        orm_mode = True
        arbitrary_types_allowed = True
        use_enum_values = True
    
    @classmethod
    def from_orm(cls, obj):
        return cls(
            id=obj.id,
            email=obj.email,
            hashed_password=obj.hashed_password,
            is_active=obj.is_active,
            created_at=obj.created_at
        )

# Usage:
# user = User(
#     email="test@example.com",
#     hashed_password="hashed_password_example"
# )
# print(user)