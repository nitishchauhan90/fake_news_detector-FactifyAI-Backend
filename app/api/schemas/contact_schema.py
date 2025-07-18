from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime

class ContactFormSchema(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    message: str = Field(..., min_length=5)
    submitted_at: datetime = Field(default_factory=datetime.utcnow)