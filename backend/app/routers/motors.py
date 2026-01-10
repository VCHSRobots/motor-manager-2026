from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from ..database import get_db
from .auth import verify_token, verify_admin_token
from ..models import Motor, MotorCreate, MotorUpdate, MotorLog, MotorLogCreate, PerformanceTestCreate, PerformanceTest
from shared.models import Motor as DBMotor, MotorLog as DBMotorLog, PerformanceTest as DBPerformanceTest
from datetime import datetime
import uuid
import os
import shutil
import json
import gzip
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


@router.post("/{motor_id}/tests", response_model=PerformanceTest)
def upload_test_data(
    motor_id: str,
    test_data: PerformanceTestCreate,
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_token)
):
    # Verify motor exists
    db_motor = db.query(DBMotor).filter(DBMotor.motor_id == motor_id).first()
    if not db_motor:
        raise HTTPException(status_code=404, detail="Motor not found")
    
    # Check if test_uuid already exists (prevent duplicate uploads)
    if test_data.test_uuid:
        existing_test = db.query(DBPerformanceTest).filter(
            DBPerformanceTest.test_uuid == test_data.test_uuid
        ).first()
        if existing_test:
            raise HTTPException(
                status_code=409, 
                detail=f"Test with UUID {test_data.test_uuid} has already been uploaded"
            )
    
    user_id = uuid.UUID(token_data['user_id'])
    
    # Create directory for test data if it doesn't exist
    test_data_dir = Path("backend/app/static/uploads/test_data")
    test_data_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate unique filename for the test data
    test_id = uuid.uuid4()
    data_filename = f"{motor_id}_{test_id}.json.gz"
    data_file_path = test_data_dir / data_filename
    
    # Save test data as compressed JSON
    test_data_json = {
        "test_date": test_data.test_date.isoformat(),
        "max_current": test_data.max_current,
        "gear_ratio": test_data.gear_ratio,
        "spool_diameter": test_data.spool_diameter,
        "weight_lbs": test_data.weight_lbs,
        "lift_direction_cw": test_data.lift_direction_cw,
        "max_lift_distance": test_data.max_lift_distance,
        "distance_lifted": test_data.distance_lifted,
        "hardware_description": test_data.hardware_description,
        "data_points": [
            {
                "timestamp": dp.timestamp,
                "voltage": dp.voltage,
                "bus_voltage": dp.bus_voltage,
                "current": dp.current,
                "rpm": dp.rpm,
                "distance": dp.distance,
                "input_power": dp.input_power,
                "output_power": dp.output_power
            }
            for dp in test_data.data_points
        ]
    }
    
    with gzip.open(data_file_path, 'wt', encoding='utf-8') as f:
        json.dump(test_data_json, f)
    
    # Create database record
    db_test = DBPerformanceTest(
        id=test_id,
        motor_id=db_motor.id,
        user_id=user_id,
        test_uuid=test_data.test_uuid,
        test_date=test_data.test_date,
        data_file_path=f"/static/uploads/test_data/{data_filename}",
        avg_power_10a=test_data.avg_power_10a,
        avg_power_20a=test_data.avg_power_20a,
        avg_power_40a=test_data.avg_power_40a,
        notes=test_data.notes
    )
    
    db.add(db_test)
    
    # Update motor's average power values to latest test results
    if test_data.avg_power_10a is not None:
        db_motor.avg_power_10a = test_data.avg_power_10a
    
    if test_data.avg_power_20a is not None:
        db_motor.avg_power_20a = test_data.avg_power_20a
    
    if test_data.avg_power_40a is not None:
        db_motor.avg_power_40a = test_data.avg_power_40a
    
    db.commit()
    db.refresh(db_test)
    
    return db_test


@router.get("/{motor_id}/tests", response_model=list[PerformanceTest])
def get_motor_tests(
    motor_id: str,
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_token)
):
    # Get motor by motor_id string
    db_motor = db.query(DBMotor).filter(DBMotor.motor_id == motor_id).first()
    if not db_motor:
        raise HTTPException(status_code=404, detail="Motor not found")
    
    tests = db.query(DBPerformanceTest).filter(
        DBPerformanceTest.motor_id == db_motor.id
    ).order_by(DBPerformanceTest.test_date.desc()).all()
    
    return tests


@router.get("/{motor_id}/tests/{test_id}/data")
def get_test_data(
    motor_id: str,
    test_id: str,
    db: Session = Depends(get_db),
    token_data: dict = Depends(verify_token)
):
    # Get motor by motor_id string
    db_motor = db.query(DBMotor).filter(DBMotor.motor_id == motor_id).first()
    if not db_motor:
        raise HTTPException(status_code=404, detail="Motor not found")
    
    # Verify test exists and belongs to motor
    db_test = db.query(DBPerformanceTest).filter(
        DBPerformanceTest.id == uuid.UUID(test_id),
        DBPerformanceTest.motor_id == db_motor.id
    ).first()
    
    if not db_test:
        raise HTTPException(status_code=404, detail="Test not found")
    
    # Read and decompress test data
    if db_test.data_file_path:
        data_file_path = Path("backend/app") / db_test.data_file_path.lstrip("/")
        
        if not data_file_path.exists():
            raise HTTPException(status_code=404, detail="Test data file not found")
        
        with gzip.open(data_file_path, 'rt', encoding='utf-8') as f:
            test_data = json.load(f)
        
        # Add avg_power values from database
        test_data['avg_power_10a'] = db_test.avg_power_10a
        test_data['avg_power_20a'] = db_test.avg_power_20a
        test_data['avg_power_40a'] = db_test.avg_power_40a
        
        return test_data
    else:
        raise HTTPException(status_code=404, detail="No test data file associated with this test")
