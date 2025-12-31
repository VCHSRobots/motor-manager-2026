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

## Deployment to DigitalOcean

### Option 1: DigitalOcean App Platform (Recommended)

1. **Create App Platform App**:
   - Go to DigitalOcean Control Panel → Apps
   - Click "Create App"
   - Connect your GitHub repository: `VCHSRobots/motor-manager-2026`
   - Select the `main` branch
   - Choose "Docker" as the source type (it will auto-detect the Dockerfile)

2. **Configure Environment**:
   - Set environment variables:
     - `DATABASE_URL`: Your Postgres connection string
     - `SHARED_PASSWORD`: Secure password for authentication
     - `PORT`: `8080` (App Platform default)

3. **Database Setup**:
   - Create a DigitalOcean Managed Database (Postgres)
   - Get the connection string and set as `DATABASE_URL`
   - Run database migrations: `python scripts/setup_db.py` (locally or via App Platform console)

4. **Deploy**:
   - App Platform will build and deploy automatically
   - Your app will be available at the generated URL

### Option 2: DigitalOcean Droplet

1. **Create Droplet**:
   - Ubuntu 22.04, 1GB RAM minimum
   - Install Docker and Docker Compose

2. **Deploy**:
   ```bash
   git clone https://github.com/VCHSRobots/motor-manager-2026.git
   cd motor-manager-2026
   cp .env.example .env
   # Edit .env with your values
   docker build -t motor-dynamo .
   docker run -p 80:8000 --env-file .env motor-dynamo
   ```

3. **Database**:
   - Use DigitalOcean Managed Database or install Postgres on the droplet

### Environment Variables

Copy `.env.example` to `.env` and fill in:

- `DATABASE_URL`: Postgres connection string
- `SHARED_PASSWORD`: Password for API authentication

### Domain Setup

Point `motors.epicteam.org` to your DigitalOcean app/droplet IP.

---

## Repository Structure

## Repository Structure

