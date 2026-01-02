from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from .auth.router import verify_admin_token
from ..models import User as UserSchema
from shared.models import User as DBUser
from pydantic import BaseModel
from typing import Optional
import uuid

router = APIRouter()

class UserResponse(BaseModel):
    id: str
    username: str
    role: str
    protected: bool
    created_at: str

    class Config:
        from_attributes = True

class UserCreate(BaseModel):
    username: str
    role: str  # "admin" or "user"

@router.get("/", response_model=list[UserResponse])
def list_users(db: Session = Depends(get_db), token_data: dict = Depends(verify_admin_token)):
    users = db.query(DBUser).all()
    return [
        UserResponse(
            id=str(user.id),
            username=user.username,
            role=user.role,
            protected=user.protected,
            created_at=str(user.created_at)
        ) for user in users
    ]

@router.post("/", response_model=UserResponse)
def create_user(user_data: UserCreate, db: Session = Depends(get_db), token_data: dict = Depends(verify_admin_token)):
    # Validate role
    if user_data.role not in ["admin", "user"]:
        raise HTTPException(status_code=400, detail="Role must be 'admin' or 'user'")
    
    # Check if username already exists
    existing = db.query(DBUser).filter(DBUser.username == user_data.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Create new user
    import hashlib
    import os
    password = os.getenv("ADMIN_PASSWORD") if user_data.role == "admin" else os.getenv("USER_PASSWORD")
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    new_user = DBUser(
        username=user_data.username,
        password_hash=password_hash,
        role=user_data.role,
        protected=False
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return UserResponse(
        id=str(new_user.id),
        username=new_user.username,
        role=new_user.role,
        protected=new_user.protected,
        created_at=str(new_user.created_at)
    )

@router.delete("/{user_id}")
def delete_user(user_id: str, db: Session = Depends(get_db), token_data: dict = Depends(verify_admin_token)):
    user = db.query(DBUser).filter(DBUser.id == uuid.UUID(user_id)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.protected:
        raise HTTPException(status_code=403, detail="Cannot delete protected admin user")
    
    db.delete(user)
    db.commit()
    return {"message": "User deleted successfully"}

@router.get("/me", response_model=UserResponse)
def get_current_user(db: Session = Depends(get_db), token_data: dict = Depends(verify_admin_token)):
    user = db.query(DBUser).filter(DBUser.id == uuid.UUID(token_data["user_id"])).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return UserResponse(
        id=str(user.id),
        username=user.username,
        role=user.role,
        protected=user.protected,
        created_at=str(user.created_at)
    )