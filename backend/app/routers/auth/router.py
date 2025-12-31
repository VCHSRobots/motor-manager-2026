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

SHARED_PASSWORD = os.getenv("SHARED_PASSWORD", "defaultpassword")  # In production, set via env

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

@router.post("/login")
def login(username: str, password: str, db: Session = Depends(get_db)):
    if password != SHARED_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Find or create user
    user = db.query(User).filter(User.username == username).first()
    if not user:
        user = User(username=username, password_hash=hash_password(SHARED_PASSWORD))
        db.add(user)
        db.commit()
        db.refresh(user)
    
    # Return a simple token (in production, use JWT)
    token = f"{user.id}:{hash_password(SHARED_PASSWORD)}"
    return {"token": token, "user_id": str(user.id)}

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        user_id, token_hash = token.split(":")
        if token_hash != hash_password(SHARED_PASSWORD):
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except:
        raise HTTPException(status_code=401, detail="Invalid token")