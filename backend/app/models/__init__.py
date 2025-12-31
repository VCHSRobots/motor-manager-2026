from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class MotorBase(BaseModel):
    name: str
    description: Optional[str] = None

class MotorCreate(MotorBase):
    pass

class Motor(MotorBase):
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class UserBase(BaseModel):
    username: str

class User(UserBase):
    id: str
    created_at: datetime

    class Config:
        from_attributes = True