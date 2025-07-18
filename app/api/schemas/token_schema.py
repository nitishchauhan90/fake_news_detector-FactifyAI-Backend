from pydantic import BaseModel
from typing import Optional


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"



class TokenData(BaseModel):
    sub: Optional[str] = None