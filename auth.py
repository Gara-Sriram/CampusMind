import os
import hashlib
import datetime
import jwt
from pymongo.database import Database

JWT_SECRET = os.getenv("JWT_SECRET")
USERS_COLLECTION = "users"

def _get_jwt_secret() -> str:
    if not JWT_SECRET:
        raise RuntimeError("JWT_SECRET environment variable is required.")
    return JWT_SECRET

def hash_password(password: str) -> tuple[str, str]:
    """Hash a password using PBKDF2-HMAC-SHA256 with a random salt."""
    salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return key.hex(), salt.hex()

def verify_password(password: str, salt_hex: str, hash_hex: str) -> bool:
    """Verify a password against its salt and stored hash."""
    try:
        salt = bytes.fromhex(salt_hex)
        key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
        return key.hex() == hash_hex
    except Exception:
        return False

def generate_token(username: str, role: str) -> str:
    """Generate a JWT token with username and role, valid for 24 hours."""
    payload = {
        "sub": username,
        "role": role,
        "exp": datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=24)
    }
    return jwt.encode(payload, _get_jwt_secret(), algorithm="HS256")

def verify_token(token: str) -> dict | None:
    """Verify and decode a JWT token."""
    try:
        return jwt.decode(token, _get_jwt_secret(), algorithms=["HS256"])
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
        return None

def get_user(db: Database, username: str) -> dict | None:
    """Get a user document by username."""
    return db[USERS_COLLECTION].find_one({"username": username})

def create_user(db: Database, username: str, password: str, role: str) -> bool:
    """Create a new user with a hashed password. Returns True on success, False if user exists."""
    if get_user(db, username):
        return False
    
    hash_hex, salt_hex = hash_password(password)
    user_doc = {
        "username": username,
        "password_hash": hash_hex,
        "password_salt": salt_hex,
        "role": role,
        "created_at": datetime.datetime.now(datetime.timezone.utc)
    }
    db[USERS_COLLECTION].insert_one(user_doc)
    return True
