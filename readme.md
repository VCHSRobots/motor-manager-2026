# Motor Dynamometer Data System

A Python-based motor dynamometer platform for running controlled tests, collecting high-rate telemetry, and managing long-term motor performance data.

This system supports:
- Windows-based dyno stations using CTRE Talon FX + CANivore
- Centralized data storage and comparison
- Web-based management, visualization, and history tracking

Hosted at: **motors.epicteam.org**

---

## System Overview

The system is split into two major components:

### 1. Dyno Station (Edge)
Runs on a Windows 11 machine connected to the dynamometer hardware.

Responsibilities:
- Control motor speed using CTRE Talon FX (closed-loop velocity)
- Execute standardized test runs (~10 s @ 100 Hz)
- Capture telemetry:
  - RPM
  - Voltage
  - Current
  - Power
  - Temperature
- Write raw time-series data to CSV / CSV.gz
- Upload run data and metadata to the cloud backend

### 2. Cloud Backend (Server)
Runs on DigitalOcean and provides data persistence and a web UI.

Responsibilities:
- Maintain a registry of motors
- Store run metadata and derived metrics
- Store raw run files in object storage
- Provide APIs for dyno stations
- Provide a web UI for:
  - Motor management
  - Run history
  - Graphing and comparisons
  - Comments and annotations

---

## Technology Stack

### Language
- **Python only**

### Dyno Station
- Windows 11
- CTRE Talon FX motor controller
- CANivore USB-to-CAN
- Phoenix 6 Python library
- CSV / CSV.gz for raw run data

### Backend
- **FastAPI** (HTTP API + web app)
- **PostgreSQL** (managed, DigitalOcean)
- **DigitalOcean Spaces** (S3-compatible object storage)
- Server-rendered UI (initially), with interactive plots

### Source Control & Deployment
- GitHub (mono-repo)
- Environment-variable configuration (12-factor style)
- Deployment via DigitalOcean App Platform or Droplet

---

## Repository Structure

