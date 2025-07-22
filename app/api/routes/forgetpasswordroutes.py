from fastapi import APIRouter, Depends, HTTPException, status, Form, Request ,Response
from fastapi.responses import RedirectResponse, HTMLResponse
from app.api.core.database import get_user_collection
from app.api.core.security import hash_password
from ..core.email import send_reset_email,generate_otp,save_otp,check_otp
from ..schemas.password_schema import OTPRequestSchema,OTPVerifySchema,ResetPasswordSchema
from ...utils.api_response import api_response
from ..core.database import get_otp_collection
router = APIRouter(prefix="/api/auth", tags=["forget Password"])

@router.post("/forget-password")
async def forget_password(
    data: OTPRequestSchema,
    response: Response,  # ✅ Add Response to set cookie
    users_collection = Depends(get_user_collection),
    otp_collection = Depends(get_otp_collection)
):
    user = users_collection.find_one({"email": data.email})
    
    if not user:
        return api_response("User not found",404)

    otp = generate_otp()
    save_otp(data.email, otp, otp_collection)
    send_reset_email(data.email, otp)

    # ✅ Set the email in cookie for future OTP verification
    response.set_cookie(
        key="otp_email",
        value=data.email,
        max_age=600,  # cookie valid for 5 minutes
        httponly=True,
        samesite="Lax"
    )

    return api_response("OTP sent successfully", 200)

# @router.post("/send-otp")
# async def send_otp(
#     payload: OTPRequestSchema,
#     otp_collection = Depends(get_otp_collection)
# ):
#     otp = generate_otp()
#     save_otp(payload.email, otp, otp_collection)

#     print(f"OTP sent to {payload.email}: {otp}")  # Replace with real email logic
#     return api_response("OTP sent successfully", 200)

from fastapi import Request

@router.post("/verify-otp")
async def verify_otp(
    request: Request,
    payload: OTPVerifySchema,
    otp_collection = Depends(get_otp_collection)
):
    # Don't use payload.email instead read from cookie
    email = request.cookies.get("otp_email")
    if not email:
        return api_response("Missing email in cookie",400)

    if check_otp(email, payload.otp, otp_collection):
        return api_response("OTP verified successfully", 200)

    return api_response("Invalid or expired OTP",400)

@router.post("/reset-password")
async def reset_password(
    payload: ResetPasswordSchema,
    request: Request,
    response: Response,
    users_collection = Depends(get_user_collection),
    otp_collection = Depends(get_otp_collection)
):
    email = request.cookies.get("otp_email")
    
    if not email:
        return api_response("OTP session expired or missing.",400)

    # Find user by email
    user = users_collection.find_one({"email": email})
    if not user:
        return api_response("User not found",404)

    # Hash and update password
    hashed = hash_password(payload.new_password)
    users_collection.update_one(
        {"email": email},
        {"$set": {"hashed_password": hashed}}
    )

    # Delete OTP record
    otp_collection.delete_one({"email": email})

    # Delete otp_email cookie (expires immediately)
    response.delete_cookie("otp_email")

    return api_response("Password reset successfully", 200)