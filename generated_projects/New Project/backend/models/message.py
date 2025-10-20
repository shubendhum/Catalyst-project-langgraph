from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID, uuid4

class Message(BaseModel):
    id: UUID = Field(default_factory=uuid4, title="Unique Identifier", description="Primary Key")
    content: str = Field(..., title="Message Content", description="The content of the message. Required.")
    timestamp: datetime = Field(default_factory=datetime.utcnow, title="Timestamp", description="Automatically generated timestamp.")

    class Config:
        # Configuration tailored for MongoDB compatibility
        json_encoders = {
            UUID: str
        }

# Sample usage
if __name__ == "__main__":
    message = Message(content="Hello, World!")
    print(message.json())