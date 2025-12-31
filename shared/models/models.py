from sqlalchemy import Column, String, Text, Float, TIMESTAMP, ForeignKey, UUID, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
import uuid
from typing import Optional


class Base(DeclarativeBase):
    pass


class Motor(Base):
    __tablename__ = "motors"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[TIMESTAMP] = mapped_column(TIMESTAMP, server_default=func.now())
    updated_at: Mapped[TIMESTAMP] = mapped_column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    # Relationships
    runs: Mapped[list["Run"]] = relationship("Run", back_populates="motor")
    comments: Mapped[list["Comment"]] = relationship("Comment", back_populates="motor")


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[TIMESTAMP] = mapped_column(TIMESTAMP, server_default=func.now())

    # Relationships
    runs: Mapped[list["Run"]] = relationship("Run", back_populates="user")
    comments: Mapped[list["Comment"]] = relationship("Comment", back_populates="user")


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