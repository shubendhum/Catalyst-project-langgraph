from datetime import datetime
from typing import Dict, Any, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, ConfigDict

class TaskListingBase(BaseModel):
    """Base model for TaskListing with common fields."""
    data: Dict[str, Any] = Field(..., description="Task data dictionary")

class TaskListingCreate(TaskListingBase):
    """Model for creating a new TaskListing."""
    user_id: UUID = Field(..., description="ID of the user who owns this task listing")

class TaskListingUpdate(BaseModel):
    """Model for updating an existing TaskListing."""
    data: Optional[Dict[str, Any]] = Field(None, description="Task data dictionary")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")

class TaskListing(TaskListingBase):
    """TaskListing model with all fields."""
    id: UUID = Field(default_factory=uuid4, description="Unique identifier for the task listing")
    user_id: UUID = Field(..., description="ID of the user who owns this task listing")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    
    model_config = ConfigDict(
        populate_by_name=True,
        validate_assignment=True,
        json_schema_extra={
            "collection": "tasklistings"
        },
        arbitrary_types_allowed=True
    )

class TaskListingInDB(TaskListing):
    """TaskListing model as stored in the database."""
    pass