import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")
EMAIL_USERNAME = os.getenv("EMAIL_USERNAME")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")
FRONTEND_URL = os.getenv("FRONTEND_URL")
SECRET_KEY = os.getenv("SECRET_KEY")
GOOGLE_CLIENT_ID=os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET=os.getenv("GOOGLE_CLIENT_SECRET")
SESSION_SECRET_KEY=os.getenv("SESSION_SECRET_KEY","supersecretfallback")
CLAIMBUSTER_API_KEY = os.getenv("CLAIMBUSTER_API_KEY")
GOOGLE_FACT_CHECK_API_KEY = os.getenv("GOOGLE_FACT_CHECK_API_KEY")
# HUGGINGFACE_API_KEY = os.getenv("HUGGINGFACE_API_KEY")
# REDIS_BROKER_URL = os.getenv("REDIS_BROKER_URL", "redis://redis:6379/0")

if not MONGO_URI or not MONGO_DB_NAME:
    raise ValueError("MONGO_URI and MONGO_DB_NAME must be set in .env file")