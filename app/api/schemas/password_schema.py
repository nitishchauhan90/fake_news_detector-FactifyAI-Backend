from pydantic import BaseModel,EmailStr,Field
from datetime import datetime

class OTPRequestSchema(BaseModel):
    email: EmailStr

class OTPVerifySchema(BaseModel):
    otp: str

class ResetPasswordSchema(BaseModel):
    new_password: str = Field(..., min_length=8)

class PasswordUpdateRequest(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=8)

class PasswordUpdateResponse(BaseModel):
    message: str