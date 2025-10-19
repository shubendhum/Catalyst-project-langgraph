from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class TaskCreationBase(BaseModel):
    """Base model for task creation data"""
    user_id: UUID
    data: Dict[str, Any]


class TaskCreationCreate(TaskCreationBase):
    """Model for creating a new task creation"""
    pass


class TaskCreationUpdate(BaseModel):
    """Model for updating an existing task creation"""
    user_id: Optional[UUID] = None
    data: Optional[Dict[str, Any]] = None


class TaskCreation(TaskCreationBase):
    """Model for a task creation document"""
    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "user_id": "123e4567-e89b-12d3-a456-426614174001",
                "data": {"task_name": "Example Task", "priority": "high"},
                "created_at": "2023-01-01T00:00:00",
                "updated_at": "2023-01-01T00:00:00"
            }
        },
        json_encoders={
            UUID: lambda v: str(v),
            datetime: lambda v: v.isoformat()
        }
    )


class TaskCreationInDB(TaskCreation):
    """Model for a task creation as stored in the database"""
    pass