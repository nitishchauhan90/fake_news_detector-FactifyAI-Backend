from fastapi import APIRouter, Response,Request,Depends,HTTPException
from app.utils.api_response import api_response
from authlib.integrations.starlette_client import OAuth
from starlette.responses import RedirectResponse
from ..core.database import get_user_collection 
from ..core.security import create_access_token
from ..core.oauth import oauth
from datetime import datetime
from ..config.config import FRONTEND_URL
router = APIRouter(prefix="/api/auth", tags=["Google auth"])

@router.post("/logout")
def logout_user(response: Response):
    response.delete_cookie("clarifyai_token")
    return api_response("User logged out successfully", 200)



@router.get("/google/login")
async def login_via_google(request: Request):
    # redirect_uri = request.url_for("google_auth_callback")
    try:
        redirect_uri = "http://localhost:8000/api/auth/google/callback"
        # print(f"Redirect URI: {redirect_uri} | Type: {type(redirect_uri)}")
        return await oauth.google.authorize_redirect(request, redirect_uri)
    except Exception as e:
        return api_response(f"Google Login failed: {str(e)}",500)


@router.get("/google/callback", name="google_auth_callback")
async def google_auth_callback(
    request: Request,
    response: Response,
    users_collection = Depends(get_user_collection)
):
    try:
        # 1. Get Google access token
        token = await oauth.google.authorize_access_token(request)
        user_info = await oauth.google.userinfo(token=token)
        email = user_info.get("email")

        if not email:
            return api_response("Email not found from Google account",400)

        # 2. Check if user exists in DB
        user = users_collection.find_one({"email": email})

        if not user:
            # 3. Create new user if not exists
            new_user = {
                "email":email,
                "username":email.split("@")[0],  # Default username
                "hashed_password":"",            # No password for Google OAuth
                # "is_active":True,
                "created_at":datetime.utcnow(),
                "oauth_provider":"google"
            }
            result = users_collection.insert_one(new_user)
            user_id = str(result.inserted_id)
            user = new_user
        else:
            user_id = str(user["_id"])

        # 4. Create JWT token
        jwt_token = create_access_token({"sub": user_id})

        # 5. Set token in cookie and redirect
        frontend_redirect_url = f"http://localhost:3000/login/callback?token={jwt_token}&user_id={user_id}"  # or your dashboard URL
        redirect_response = RedirectResponse(url=frontend_redirect_url)
        redirect_response.set_cookie(
            key="clarifyai_token",
            value=jwt_token,
            httponly=True,
            secure=False,  # True in production with HTTPS
            samesite="lax"
        )

        
        return redirect_response
    except Exception as e:
        return api_response(f"Google OAuth failed: {str(e)}",400)