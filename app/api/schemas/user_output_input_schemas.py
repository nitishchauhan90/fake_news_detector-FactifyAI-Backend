from pydantic import BaseModel, EmailStr, Field
from typing import Optional
import datetime

class ClaimRequest(BaseModel):
    text: str