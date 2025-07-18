from pydantic import BaseModel


class PasswordUpdateRequest(BaseModel):
    old_password: str
    new_password: str

class PasswordUpdateResponse(BaseModel):
    message: str