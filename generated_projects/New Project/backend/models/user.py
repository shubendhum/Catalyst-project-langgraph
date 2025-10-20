from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from uuid import UUID, uuid4
from typing import Optional

class User(BaseModel):
    id: UUID = Field(default_factory=uuid4, alias="_id")  # UUID generation for primary key
    email: EmailStr
    hashed_password: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        # Allow for database compatibility with MongoDB (using `_id` for UUID)
        allow_population_by_field_name = True  # Allow population using the alias
        orm_mode = True  # Enable ORM mode for compatibility with ORMs like SQLAlchemy

# Example on how to create a User object
# user_instance = User(email='user@example.com', hashed_password='secure_password_hash')