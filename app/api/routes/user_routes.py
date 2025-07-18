from fastapi import APIRouter,Depends,HTTPException ,Response
from bson import ObjectId
from ..core.database import get_user_collection
from ..core.security import verify_password,hash_password,create_access_token
from ..core.oauth import get_current_user
from fastapi.security import OAuth2PasswordRequestForm
import datetime
from app.utils.api_response import api_response
from fastapi.encoders import jsonable_encoder
from ..schemas.user_schema import (
    UserCreate,
    UserInDB,
    UserPublic,
)
from ..schemas.password_schema import(
    PasswordUpdateRequest,
    PasswordUpdateResponse,
)
from ..schemas.token_schema import(
    TokenResponse,
)

router = APIRouter(prefix="/api/auth", tags=["user"])

# Helper to sanitize MongoDB user data
def sanitize_user(user):
    user["id"] = str(user.pop("_id"))
    user.pop("hashed_password", None)
    return user


@router.post("/register", response_model=dict)
async def register_user(user_data: UserCreate, users_collection=Depends(get_user_collection)):
    if users_collection.find_one({"email": user_data.email}):
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_pw = hash_password(user_data.password)
    user_dict = user_data.dict()
    user_dict.pop("password")
    user_dict["hashed_password"] = hashed_pw
    user_dict["is_active"] = True
    user_dict["created_at"] = datetime.datetime.utcnow()
    result = users_collection.insert_one(user_dict)
    user_dict["_id"] = result.inserted_id
    return api_response("User registered successfully", 201, sanitize_user(user_dict))


@router.post("/login", response_model=dict)
async def login_user(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    users_collection=Depends(get_user_collection)
):
    user = users_collection.find_one({"email": form_data.username})
    if not user or not verify_password(form_data.password, user.get("hashed_password")):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_access_token({"sub": str(user["_id"])})
    response.set_cookie(
        key="clarifyai_token",
        value=token,
        httponly=True,
        max_age=1800
    )
    return api_response("Login successful", 200, {"access_token": token, "token_type": "bearer"})

@router.put("/update", response_model=dict)
async def update_user_fields(
    updated_data: UserPublic,
    current_user=Depends(get_current_user),
    users_collection=Depends(get_user_collection)
):
    user_id = current_user.get("sub")
    update_fields = jsonable_encoder(updated_data)
    await users_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": update_fields}
    )
    user = await users_collection.find_one({"_id": ObjectId(user_id)})
    return api_response("User updated", 200, sanitize_user(user))

@router.put("/update-password", response_model=dict)
async def update_user_password(
    password_data: PasswordUpdateRequest,
    current_user=Depends(get_current_user),
    users_collection=Depends(get_user_collection)
):
    user_id = current_user.get("sub")
    user = users_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not verify_password(password_data.old_password, user.get("hashed_password")):
        raise HTTPException(status_code=401, detail="Old password is incorrect")
    new_hashed = hash_password(password_data.new_password)
    users_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"hashed_password": new_hashed}}
    )
    return api_response("Password updated successfully", 200)

@router.delete("/delete", response_model=dict)
async def delete_user_account(current_user=Depends(get_current_user), users_collection=Depends(get_user_collection)):
    user_id = current_user.get("sub")
    result = users_collection.delete_one({"_id": ObjectId(user_id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return api_response("User account deleted successfully", 200)

@router.get("/{user_id}", response_model=dict)
async def get_user_by_id(user_id: str, users_collection=Depends(get_user_collection)):
    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=400, detail="Invalid user ID format")
    user = users_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return api_response("User fetched", 200, sanitize_user(user))
