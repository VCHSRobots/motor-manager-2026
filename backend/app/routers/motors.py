from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from .auth import verify_token
from ..models import Motor, MotorCreate
import shared.models
from shared.models import Motor as DBMotor
import uuid

router = APIRouter()

@router.get("/", response_model=list[Motor])
def get_motors(db: Session = Depends(get_db), user_id: str = Depends(verify_token)):
    motors = db.query(DBMotor).all()
    return motors

@router.post("/", response_model=Motor)
def create_motor(motor: MotorCreate, db: Session = Depends(get_db), user_id: str = Depends(verify_token)):
    db_motor = DBMotor(**motor.model_dump())
    db.add(db_motor)
    db.commit()
    db.refresh(db_motor)
    return db_motor

@router.get("/{motor_id}", response_model=Motor)
def get_motor(motor_id: str, db: Session = Depends(get_db), user_id: str = Depends(verify_token)):
    motor = db.query(DBMotor).filter(DBMotor.id == uuid.UUID(motor_id)).first()
    if not motor:
        raise HTTPException(status_code=404, detail="Motor not found")
    return motor