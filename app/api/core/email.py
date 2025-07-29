import smtplib
from email.message import EmailMessage
import random
from ..config.config import EMAIL_USERNAME,EMAIL_PASSWORD
from pymongo.collection import Collection
from datetime import datetime , timedelta

def generate_otp() -> str:
    return str(random.randint(1000, 9999))

def send_reset_email(to_email,otp,message):
    email_user = EMAIL_USERNAME
    email_pass = EMAIL_PASSWORD

    msg = EmailMessage()
    msg["Subject"] = message
    msg["From"] = email_user
    msg["To"] = to_email
    msg.set_content(f"OTP to {message}: {otp}")

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(email_user, email_pass)
        smtp.send_message(msg)




def save_otp(email: str, otp: str, collection: Collection):
    expires_at = datetime.utcnow() + timedelta(minutes=5)
    collection.update_one(
        {"email": email},
        {"$set": {
            "otp": otp,
            "expires_at": expires_at,
            "is_verified": False
        }},
        upsert=True
    )

def check_otp(email: str, otp: str, collection: Collection) -> bool:
    record = collection.find_one({"email": email})
    if not record:
        return False
    if record.get("otp") != otp:
        return False
    if record.get("expires_at") < datetime.utcnow():
        return False
    return True

