from fastapi import APIRouter, Depends, HTTPException, status, Form, Request
from fastapi.responses import RedirectResponse, HTMLResponse
from app.api.core.database import get_user_collection
from app.api.core.security import hash_password
from app.utils.api_response import api_response
from bson import ObjectId
import uuid
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText

router = APIRouter(prefix="/api/auth", tags=["forget Password"])

# Simulated in-memory token store (Use Redis or DB in production)
reset_tokens = {}

SMTP_SERVER = "smtp.example.com"
SMTP_PORT = 587
SMTP_USERNAME = "your_email@example.com"
SMTP_PASSWORD = "your_password"

@router.post("/forgot-password")
async def forgot_password(email: str = Form(...), users_collection=Depends(get_user_collection)):
    user = users_collection.find_one({"email": email})
    if not user:
        raise HTTPException(status_code=404, detail="Email not registered")
    token = str(uuid.uuid4())
    reset_tokens[token] = {
        "user_id": str(user["_id"]),
        "expires": datetime.utcnow() + timedelta(minutes=15)
    }
    reset_link = f"http://localhost:8000/api/auth/reset-password?token={token}"
    send_email(email, "Password Reset", f"Click this link to reset your password: {reset_link}")
    return api_response("Password reset link sent to your email", 200)

@router.get("/reset-password")
async def reset_password_form(token: str):
    if token not in reset_tokens or reset_tokens[token]["expires"] < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    html_content = f"""
    <html>
    <body>
        <form action="/api/auth/reset-password" method="post">
            <input type="hidden" name="token" value="{token}" />
            New Password: <input type="password" name="new_password" required /><br>
            <button type="submit">Change Password</button>
        </form>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@router.post("/reset-password")
async def reset_password(token: str = Form(...), new_password: str = Form(...), users_collection=Depends(get_user_collection)):
    if token not in reset_tokens or reset_tokens[token]["expires"] < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    user_id = reset_tokens[token]["user_id"]
    hashed_pw = hash_password(new_password)
    users_collection.update_one({"_id": ObjectId(user_id)}, {"$set": {"hashed_password": hashed_pw}})

    del reset_tokens[token]
    return RedirectResponse(url="/login", status_code=303)


def send_email(to_email: str, subject: str, body: str):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = SMTP_USERNAME
    msg["To"] = to_email

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.sendmail(SMTP_USERNAME, to_email, msg.as_string())
