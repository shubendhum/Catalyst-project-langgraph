from pydantic import BaseModel, Field, constr
from uuid import UUID
from typing import Dict, Any, Optional
from datetime import datetime

class InteractiveButton(BaseModel):
    id: UUID = Field(..., description="Unique identifier for the interactive button")
    user_id: Optional[UUID] = Field(None, description="User ID associated with the button", foreign_key="User")
    data: Dict[str, Any] = Field(..., description="Data associated with the interactive button")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp when button was created")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp when button was last updated")

    class Config:
        orm_mode = True  # Allows conversion from ORM models
        arbitrary_types_allowed = True  # Allows arbitrary types for MongoDB compatibility