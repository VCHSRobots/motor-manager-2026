from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from ...database import get_db
import shared.models
from shared.models import User
import os
import hashlib
import time

router = APIRouter()
security = HTTPBearer()

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin_default")
USER_PASSWORD = os.getenv("USER_PASSWORD", "user_default")
TOKEN_EXPIRY_HOURS = 2

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def generate_token(user_id: str, role: str, password: str) -> str:
    """Generate a token with user_id, role, timestamp, and password hash"""
    timestamp = int(time.time())
    token_hash = hash_password(password)
    return f"{user_id}:{role}:{timestamp}:{token_hash}"

@router.post("/login")
def login(username: str, password: str, db: Session = Depends(get_db)):
    # Determine role based on password
    if password == ADMIN_PASSWORD:
        role = "admin"
    elif password == USER_PASSWORD:
        role = "user"
    else:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Find or create user with the appropriate role
    user = db.query(User).filter(User.username == username).first()
    if not user:
        user = User(
            username=username, 
            password_hash=hash_password(password),
            role=role
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    # Return token with role and timestamp
    token = generate_token(str(user.id), role, password)
    return {
        "token": token, 
        "user_id": str(user.id),
        "username": user.username,
        "role": role
    }

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    from fastapi import Request
    from starlette.requests import Request as StarletteRequest
    
    token = credentials.credentials
    try:
        user_id, role, timestamp, token_hash = token.split(":")
        
        # Check if token has expired (2 hours)
        current_time = int(time.time())
        token_age = current_time - int(timestamp)
        expiry_seconds = TOKEN_EXPIRY_HOURS * 3600
        
        if token_age > expiry_seconds:
            raise HTTPException(status_code=401, detail="Token expired. Please login again.")
        
        # Verify token hash matches one of the passwords
        if token_hash != hash_password(ADMIN_PASSWORD) and token_hash != hash_password(USER_PASSWORD):
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Generate a new token with refreshed timestamp for activity-based renewal
        # Determine which password to use based on which hash matched
        if token_hash == hash_password(ADMIN_PASSWORD):
            new_token = generate_token(user_id, role, ADMIN_PASSWORD)
        else:
            new_token = generate_token(user_id, role, USER_PASSWORD)
        
        return {"user_id": user_id, "role": role, "new_token": new_token}
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid token format")
    except HTTPException:
        raise
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

def verify_admin_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token_data = verify_token(credentials)
    if token_data["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return token_data

def verify_admin_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token_data = verify_token(credentials)
    if token_data["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return token_data