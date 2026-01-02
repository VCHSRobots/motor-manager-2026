from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date
import uuid


class MotorCreate(BaseModel):
    name: str
    motor_type: Optional[str] = None
    date_of_purchase: Optional[date] = None
    purchase_season: Optional[str] = None
    purchase_year: Optional[int] = None
    status: str = "On Order"


class MotorUpdate(BaseModel):
    name: Optional[str] = None
    motor_type: Optional[str] = None
    date_of_purchase: Optional[date] = None
    purchase_season: Optional[str] = None
    purchase_year: Optional[int] = None
    picture_path: Optional[str] = None
    status: Optional[str] = None
    peak_power_10a: Optional[float] = None
    peak_power_20a: Optional[float] = None
    peak_power_30a: Optional[float] = None
    peak_power_40a: Optional[float] = None


class Motor(BaseModel):
    id: uuid.UUID
    motor_id: Optional[str] = None
    name: str
    motor_type: Optional[str] = None
    date_of_purchase: Optional[date] = None
    purchase_season: Optional[str] = None
    purchase_year: Optional[int] = None
    picture_path: Optional[str] = None
    status: str
    peak_power_10a: Optional[float] = None
    peak_power_20a: Optional[float] = None
    peak_power_30a: Optional[float] = None
    peak_power_40a: Optional[float] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class MotorLogCreate(BaseModel):
    entry_text: str


class MotorLog(BaseModel):
    id: uuid.UUID
    motor_id: uuid.UUID
    user_id: uuid.UUID
    entry_text: str
    created_at: datetime

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    username: str
    password: str
    role: str = "user"


class User(BaseModel):
    id: uuid.UUID
    username: str
    role: str
    protected: bool
    created_at: datetime

    class Config:
        from_attributes = True
