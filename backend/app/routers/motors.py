from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from ..database import get_db
from .auth import verify_token, verify_admin_token
from ..models import Motor, MotorCreate, MotorUpdate, MotorLog, MotorLogCreate
from shared.models import Motor as DBMotor, MotorLog as DBMotorLog
from datetime import datetime
import uuid
import os
import shutil
from pathlib import Path

router = APIRouter()

# Directory for storing uploaded files
UPLOAD_DIR = Path("backend/app/static/uploads/motors")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

def generate_motor_id(db: Session) -> str:
    """Generate motor ID in format yyyy-nnn"""
    current_year = datetime.now().year
    
    # Find the highest sequence number for this year
    motors_this_year = db.query(DBMotor).filter(
        DBMotor.motor_id.like(f"{current_year}-%")
    ).all()
    
    if not motors_this_year:
        sequence = 1
    else:
        sequences = [int(m.motor_id.split('-')[1]) for m in motors_this_year if m.motor_id]
        sequence = max(sequences) + 1
    
    return f"{current_year}-{sequence:03d}"

@router.get("/", response_model=list[Motor])
def get_motors(db: Session = Depends(get_db), token_data: dict = Depends(verify_token)):
    motors = db.query(DBMotor).all()
    return motors

@router.post("/", response_model=Motor)
def create_motor(motor: MotorCreate, db: Session = Depends(get_db), token_data: dict = Depends(verify_token)):
    # Create motor without motor_id first
    motor_data = motor.model_dump(exclude_unset=True)
    db_motor = DBMotor(**motor_data)
    
    # If type is provided, assign motor_id (name is now optional)
    if motor.motor_type:
        db_motor.motor_id = generate_motor_id(db)
    
    db.add(db_motor)
    db.commit()
    db.refresh(db_motor)
    return db_motor

@router.get("/{motor_id}", response_model=Motor)
def get_motor(motor_id: str, db: Session = Depends(get_db), token_data: dict = Depends(verify_token)):
    motor = db.query(DBMotor).filter(DBMotor.id == uuid.UUID(motor_id)).first()
    if not motor:
        raise HTTPException(status_code=404, detail="Motor not found")
    return motor

@router.put("/{motor_id}", response_model=Motor)
def update_motor(motor_id: str, motor: MotorUpdate, db: Session = Depends(get_db), token_data: dict = Depends(verify_token)):
    db_motor = db.query(DBMotor).filter(DBMotor.id == uuid.UUID(motor_id)).first()
    if not db_motor:
        raise HTTPException(status_code=404, detail="Motor not found")
    
    # Update fields
    update_data = motor.model_dump(exclude_unset=True)
    
    # If motor doesn't have ID yet and now has basic info, assign it
    if not db_motor.motor_id and motor.name and motor.motor_type:
        db_motor.motor_id = generate_motor_id(db)
    
    for key, value in update_data.items():
        setattr(db_motor, key, value)
    
    db.commit()
    db.refresh(db_motor)
    return db_motor

@router.delete("/{motor_id}")
def delete_motor(motor_id: str, db: Session = Depends(get_db), token_data: dict = Depends(verify_admin_token)):
    db_motor = db.query(DBMotor).filter(DBMotor.id == uuid.UUID(motor_id)).first()
    if not db_motor:
        raise HTTPException(status_code=404, detail="Motor not found")
    
    db.delete(db_motor)
    db.commit()
    return {"message": "Motor deleted successfully"}

@router.get("/{motor_id}/logs", response_model=list[MotorLog])
def get_motor_logs(motor_id: str, db: Session = Depends(get_db), token_data: dict = Depends(verify_token)):
    logs = db.query(DBMotorLog).filter(
        DBMotorLog.motor_id == uuid.UUID(motor_id)
    ).order_by(DBMotorLog.created_at.desc()).all()
    return logs

@router.post("/{motor_id}/logs", response_model=MotorLog)
def create_motor_log(motor_id: str, log: MotorLogCreate, db: Session = Depends(get_db), token_data: dict = Depends(verify_token)):
    user_id = uuid.UUID(token_data['user_id'])
    
    db_log = DBMotorLog(
        motor_id=uuid.UUID(motor_id),
        user_id=user_id,
        entry_text=log.entry_text
    )
    
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log

@router.post("/{motor_id}/upload-picture")
async def upload_motor_picture(
    motor_id: str, 
    file: UploadFile = File(...),
    db: Session = Depends(get_db), 
    token_data: dict = Depends(verify_token)
):
    # Validate file type
    allowed_types = {"image/jpeg", "image/png", "image/gif", "image/webp"}
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Invalid file type. Only images are allowed.")
    
    # Get motor
    db_motor = db.query(DBMotor).filter(DBMotor.id == uuid.UUID(motor_id)).first()
    if not db_motor:
        raise HTTPException(status_code=404, detail="Motor not found")
    
    # Generate unique filename
    file_extension = file.filename.split(".")[-1]
    unique_filename = f"{motor_id}.{file_extension}"
    file_path = UPLOAD_DIR / unique_filename
    
    # Save file
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Update motor with picture path
    db_motor.picture_path = f"/static/uploads/motors/{unique_filename}"
    db.commit()
    
    return {"picture_path": db_motor.picture_path}