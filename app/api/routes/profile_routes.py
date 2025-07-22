from fastapi import APIRouter, Depends,HTTPException
from ..core.oauth import get_current_user
from bson import ObjectId
from ...utils.api_response import api_response
from ..core.database import get_user_collection

router = APIRouter(prefix="/api/auth", tags=["profile"])

def sanitize_user(user):
    user["id"] = str(user.pop("_id"))
    user.pop("hashed_password", None)
    return user

@router.get("/profile/me", response_model=dict)
async def get_my_profile(current_user=Depends(get_current_user), users_collection=Depends(get_user_collection)):
    user_id = current_user.get("sub")
    # print("Decoded token payload:", current_user)
    user = users_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        return api_response("User not found",404)
    # if not isinstance(user_id, str) or not ObjectId.is_valid(user_id):
    #     raise HTTPException(status_code=400, detail="Invalid user ID format")
    return api_response("Profile fetched", 200, sanitize_user(user))

