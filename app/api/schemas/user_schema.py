from pydantic import BaseModel, EmailStr, Field
from typing import Optional
import datetime

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class UserInDB(UserBase):
    hashed_password: str
    is_active: bool = True
    created_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)

class UserPublic(UserBase):
    is_active: bool
    created_at: datetime.datetime
