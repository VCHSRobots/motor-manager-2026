from sqlalchemy import Column, String, Text, Float, TIMESTAMP, ForeignKey, UUID, func, Integer, Date
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
import uuid
from typing import Optional
from datetime import datetime


class Base(DeclarativeBase):
    pass


class Motor(Base):
    __tablename__ = "motors"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    motor_id: Mapped[Optional[str]] = mapped_column(String(20), unique=True)  # yyyy-nnn format
    name: Mapped[Optional[str]] = mapped_column(String(255))
    motor_type: Mapped[Optional[str]] = mapped_column(String(255))
    date_of_purchase: Mapped[Optional[Date]] = mapped_column(Date)
    purchase_season: Mapped[Optional[str]] = mapped_column(String(50))  # Fall, Spring, Summer, Winter
    purchase_year: Mapped[Optional[int]] = mapped_column(Integer)
    picture_path: Mapped[Optional[str]] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(String(50), server_default="On Order", nullable=False)
    
    # Average power measurements (watts at different current limits)
    avg_power_10a: Mapped[Optional[float]] = mapped_column(Float)
    avg_power_20a: Mapped[Optional[float]] = mapped_column(Float)
    avg_power_40a: Mapped[Optional[float]] = mapped_column(Float)
    
    created_at: Mapped[TIMESTAMP] = mapped_column(TIMESTAMP, server_default=func.now())
    updated_at: Mapped[TIMESTAMP] = mapped_column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    # Relationships
    runs: Mapped[list["Run"]] = relationship("Run", back_populates="motor", cascade="all, delete-orphan")
    comments: Mapped[list["Comment"]] = relationship("Comment", back_populates="motor", cascade="all, delete-orphan")
    log_entries: Mapped[list["MotorLog"]] = relationship("MotorLog", back_populates="motor", cascade="all, delete-orphan")
    performance_tests: Mapped[list["PerformanceTest"]] = relationship("PerformanceTest", back_populates="motor", cascade="all, delete-orphan")


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), server_default="user", nullable=False)
    protected: Mapped[bool] = mapped_column(server_default="false", nullable=False)
    created_at: Mapped[TIMESTAMP] = mapped_column(TIMESTAMP, server_default=func.now())

    # Relationships
    runs: Mapped[list["Run"]] = relationship("Run", back_populates="user")
    comments: Mapped[list["Comment"]] = relationship("Comment", back_populates="user")
    log_entries: Mapped[list["MotorLog"]] = relationship("MotorLog", back_populates="user")
    performance_tests: Mapped[list["PerformanceTest"]] = relationship("PerformanceTest", back_populates="user")


class Run(Base):
    __tablename__ = "runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    motor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("motors.id"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    timestamp: Mapped[TIMESTAMP] = mapped_column(TIMESTAMP, nullable=False)
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float)
    data_file_key: Mapped[Optional[str]] = mapped_column(String(500))
    avg_rpm: Mapped[Optional[float]] = mapped_column(Float)
    peak_power: Mapped[Optional[float]] = mapped_column(Float)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[TIMESTAMP] = mapped_column(TIMESTAMP, server_default=func.now())

    # Relationships
    motor: Mapped["Motor"] = relationship("Motor", back_populates="runs")
    user: Mapped["User"] = relationship("User", back_populates="runs")
    comments: Mapped[list["Comment"]] = relationship("Comment", back_populates="run")


class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    motor_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("motors.id"))
    run_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("runs.id"))
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[TIMESTAMP] = mapped_column(TIMESTAMP, server_default=func.now())

    # Relationships
    motor: Mapped[Optional["Motor"]] = relationship("Motor", back_populates="comments")
    run: Mapped[Optional["Run"]] = relationship("Run", back_populates="comments")
    user: Mapped["User"] = relationship("User", back_populates="comments")


class MotorLog(Base):
    __tablename__ = "motor_logs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    motor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("motors.id"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    entry_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[TIMESTAMP] = mapped_column(TIMESTAMP, server_default=func.now())

    # Relationships
    motor: Mapped["Motor"] = relationship("Motor", back_populates="log_entries")
    user: Mapped["User"] = relationship("User", back_populates="log_entries")


class PerformanceTest(Base):
    __tablename__ = "performance_tests"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    motor_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("motors.id"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    test_uuid: Mapped[Optional[str]] = mapped_column(String(36), unique=True, index=True)  # Client-generated UUID for deduplication
    test_date: Mapped[TIMESTAMP] = mapped_column(TIMESTAMP, nullable=False)
    data_file_path: Mapped[Optional[str]] = mapped_column(String(500))
    
    # Average power measurements from this test
    avg_power_10a: Mapped[Optional[float]] = mapped_column(Float)
    avg_power_20a: Mapped[Optional[float]] = mapped_column(Float)
    avg_power_40a: Mapped[Optional[float]] = mapped_column(Float)
    
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[TIMESTAMP] = mapped_column(TIMESTAMP, server_default=func.now())

    # Relationships
    motor: Mapped["Motor"] = relationship("Motor", back_populates="performance_tests")
    user: Mapped["User"] = relationship("User", back_populates="performance_tests")