from fastapi import APIRouter, Response
from app.utils.api_response import api_response

router = APIRouter(prefix="/api/auth", tags=["Auth"])

@router.post("/logout")
def logout_user(response: Response):
    response.delete_cookie("clarifyai_token")
    return api_response("User logged out successfully", 200)