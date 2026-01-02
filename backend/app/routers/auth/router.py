from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from ...database import get_db
import shared.models
from shared.models import User
import os
import hashlib

router = APIRouter()
security = HTTPBearer()

ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin_default")
USER_PASSWORD = os.getenv("USER_PASSWORD", "user_default")

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

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
    
    # Return token with role information
    token = f"{user.id}:{role}:{hash_password(password)}"
    return {
        "token": token, 
        "user_id": str(user.id),
        "username": user.username,
        "role": role
    }

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        user_id, role, token_hash = token.split(":")
        # Verify token hash matches one of the passwords
        if token_hash != hash_password(ADMIN_PASSWORD) and token_hash != hash_password(USER_PASSWORD):
            raise HTTPException(status_code=401, detail="Invalid token")
        return {"user_id": user_id, "role": role}
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

def verify_admin_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token_data = verify_token(credentials)
    if token_data["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return token_data