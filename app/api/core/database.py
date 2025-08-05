from pymongo import MongoClient
import certifi
from ..config import config

client = MongoClient(config.MONGO_URI,tlsCAFile=certifi.where())
db = client.get_database(config.MONGO_DB_NAME)

# Dependency function for injecting db instance
def get_database():
    return db

# Dependency function for injecting user collection
def get_user_collection():

    return db["user_collection"]

def get_contact_collection():
    db = get_database()  # Your database client logic
    return db["contact_forms"]

def get_otp_collection():
    db = get_database()
    return db["otp_collection"]

def get_ip_collection():
    return db["ip_limits"]

def get_feedback_collection():
    return db["feedback_collection"]