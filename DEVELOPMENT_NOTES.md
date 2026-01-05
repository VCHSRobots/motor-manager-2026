# Development Notes - Motor Manager 2026

**Last Updated:** January 4, 2026  
**Project Status:** Deployed and operational  
**Live URL:** http://motors.epicteam.org

---

## Recent Changes (January 4, 2026)

### 1. Test UUID Duplicate Prevention System
**Problem:** Tests could be uploaded multiple times, creating duplicate data.

**Solution Implemented:**
- Each test now generates a unique UUID when it starts (`uuid.uuid4()`)
- Client-side tracking in `uploaded_tests.json` file
- Server-side validation with database unique constraint
- Upload button automatically disabled after successful upload

**Files Modified:**
- `motor_test_app.py` - Added UUID generation, tracking functions
- `backend/app/models/__init__.py` - Added `test_uuid` field to PerformanceTestCreate
- `backend/app/routers/motors.py` - Added duplicate check (HTTP 409 if duplicate)
- `shared/models/models.py` - Added `test_uuid` column to database
- `scripts/migrate_add_test_uuid.py` - Migration script to add column
- `deploy.sh` - Added migration to deployment process

**How It Works:**
1. Test starts → UUID generated (e.g., "a1b2c3d4-e5f6-7890-abcd-ef1234567890")
2. First upload → Succeeds, UUID stored in database and local file
3. Upload button disabled
4. Subsequent attempts → Blocked by client check or server returns 409 error

### 2. Motor Detail Page UI Improvements
**Goal:** Make layout more compact, fit graph "above the fold"

**Changes Made:**
- Motor picture integrated into top section (reduced from 400x400px to 200x200px)
- Removed separate "Motor Picture" card
- Average power metrics moved inline with status badge and purchase date
- Test selector made more compact (inline label + dropdown)
- Test metadata condensed to single-line layout
- Reduced padding throughout (cards: 2rem → 1.5rem)
- Container top margin reduced (2rem → 1rem)
- Back link margin reduced and font size decreased

**Files Modified:**
- `backend/app/templates/motor_detail.html`

**Result:** Graph now visible without scrolling on most screens.

### 3. Deployment Configuration
**Current Setup:**
- Deployed to DigitalOcean droplet
- Docker Compose with 2 services: app + postgres
- Domain: motors.epicteam.org
- Fresh database deployment (all data wiped on update)

**Environment Variables Required (.env):**
```env
DATABASE_URL=postgresql://motor_user:PASSWORD@postgres:5432/dynamometer_db
POSTGRES_PASSWORD=PASSWORD
ADMIN_PASSWORD=your_admin_password
USER_PASSWORD=your_user_password
DEFAULT_ADMIN_USERNAME=admin
```

**Deployment Process:**
```bash
ssh root@YOUR_DROPLET_IP
cd motor-manager-2026
git checkout -- deploy.sh  # If conflicts
git pull origin main
./deploy.sh
# Type 'yes' when prompted
```

---

## Windows Motor Test Application

### Overview
- **File:** `motor_test_app.py`
- **Purpose:** Standalone Windows app for running motor dynamometer tests
- **Hardware:** Connects to CANivore and Talon FX motors via CTRE Phoenix 6

### Features
- Real-time motor testing with RPM and current control
- Live graph display during tests
- Automatic average power calculation at 90% target RPM
- CSV export of test data
- Upload results to web server
- UUID-based duplicate prevention

### Configuration
Settings stored in `motor_test_config.json`:
- Server URL (http://motors.epicteam.org)
- Username/password for authentication
- Gear ratio (default: 1.0)
- Flywheel inertia (default: 0.0256 kg·m²)
- Hardware description
- Device ID for Talon FX (default: 1)

### Building Executable
**Files:**
- `build_app.bat` - Creates single .exe file (may have CANivore issues)
- `build_app_folder.bat` - Creates folder with dependencies (recommended for hardware)
- `motor_icon.svg` - Source SVG for icon
- `motor_icon.ico` - Windows icon file

**Known Issue:** CANivore connection fails with `--onefile` builds.  
**Solution:** Use `build_app_folder.bat` which creates folder-based distribution.

**Build Command:**
```bash
# Install PyInstaller first
pip install pyinstaller

# Build (folder-based, best for hardware)
build_app_folder.bat

# Output: dist\EPIC Motor Test\EPIC Motor Test.exe
```

---

## Architecture Overview

### Backend (FastAPI)
**Location:** `backend/app/`

**Key Files:**
- `main.py` - FastAPI app initialization, creates tables on startup
- `database.py` - Database connection and session management
- `routers/auth.py` - Login endpoint (returns token)
- `routers/motors.py` - Motor CRUD, test upload/retrieval
- `routers/users.py` - User management
- `models/__init__.py` - Pydantic models for API validation

**Database Models:**
**Location:** `shared/models/models.py`
- User (username, password_hash, role, protected)
- Motor (motor_id, motor_type, status, avg_power_10a/20a/40a, picture_path)
- MotorLog (entry_text, created_at)
- PerformanceTest (test_uuid, test_date, avg_power values, data_file_path)

**Test Data Storage:**
- Compressed JSON: `backend/app/static/uploads/test_data/{motor_id}_{test_id}.json.gz`
- Database: performance_tests table stores metadata + avg_power results
- File naming: motor_id is string (e.g., "2026-001"), test_id is UUID

### Frontend (HTML/JavaScript)
**Location:** `backend/app/templates/`

**Pages:**
- `index.html` - Login page
- `motors.html` - Motor inventory list with filters
- `motor_detail.html` - Individual motor view with tests and graphs
- `manage_users.html` - Admin user management

**JavaScript:**
- `static/js/auth-utils.js` - authFetch() wrapper with token refresh
- Chart.js for performance graphs (4 Y-axes: RPM, Current, Voltage, Power)

**Authentication:**
- JWT tokens stored in localStorage
- 2-hour expiration with activity-based renewal
- X-New-Token header for automatic refresh

---

## Database Migrations

**Location:** `scripts/`

**Migration Files:**
1. `migrate_role_protected.py` - Added role and protected fields to users
2. `migrate_name_optional.py` - Made motor name optional
3. `migrate_power_columns.py` - Renamed peak_power → avg_power
4. `migrate_add_test_uuid.py` - Added test_uuid column (NEW)

**Running Migrations:**
- Automatically run by `deploy.sh` on droplet
- Local testing: Set environment variables, run `python scripts/migrate_*.py`

---

## Known Issues & Limitations

### 1. PyInstaller + CANivore
**Issue:** Single-file executable (`--onefile`) doesn't connect to CANivore  
**Workaround:** Use folder-based build with `--collect-all phoenix6`

### 2. Motor ID Assignment
**Behavior:** Motor ID auto-assigned on creation (format: "YYYY-XXX")  
**Note:** Cannot be changed after creation

### 3. Test Data Deletion
**Current:** No way to delete individual tests from UI  
**Workaround:** Admin can delete from database directly

### 4. No HTTPS
**Current:** Running on HTTP only  
**Future:** Add Let's Encrypt SSL certificate for HTTPS

---

## Development Workflow

### Local Development
```bash
# Backend
python run_server.py
# Access at http://localhost:8000

# Database (local PostgreSQL required)
# Set environment variables in .env file
python scripts/setup_db.py  # First time only
```

### Testing Changes
1. Make code changes
2. Test locally
3. Commit to git
4. Push to GitHub
5. Deploy to droplet with `./deploy.sh`

### Adding New Features
1. Update database models in `shared/models/models.py` if needed
2. Create migration script in `scripts/` if schema changes
3. Update API models in `backend/app/models/__init__.py`
4. Update routers in `backend/app/routers/`
5. Update frontend templates
6. Test locally
7. Add migration to `deploy.sh`
8. Deploy

---

## API Endpoints

### Authentication
- `POST /auth/login` - Login (params: username, password) → returns token

### Motors
- `GET /motors` - List all motors
- `POST /motors` - Create motor
- `GET /motors/{id}` - Get motor by UUID
- `PUT /motors/{id}` - Update motor
- `DELETE /motors/{id}` - Delete motor (admin only)
- `POST /motors/{id}/picture` - Upload picture
- `GET /motors/{motor_id}/logs` - Get motor logs (motor_id is string like "2026-001")
- `POST /motors/{motor_id}/logs` - Add log entry

### Performance Tests
- `POST /motors/{motor_id}/tests` - Upload test data (motor_id is string)
- `GET /motors/{motor_id}/tests` - List tests for motor
- `GET /motors/{motor_id}/tests/{test_id}/data` - Get test data with decompressed JSON

### Users
- `GET /users` - List users
- `POST /users` - Create user
- `PUT /users/{id}` - Update user
- `DELETE /users/{id}` - Delete user (cannot delete protected admin)

---

## Important Notes

### Motor ID vs UUID
**Confusion Point:** Motors have TWO identifiers
- `id` - UUID primary key (e.g., "123e4567-e89b-12d3-a456-426614174000")
- `motor_id` - Display string (e.g., "2026-001")

**Frontend Usage:**
- URL uses UUID: `/motor/{UUID}`
- API calls for tests use motor_id string
- JavaScript variable: `motorIdString` stores the motor_id

### Authentication Details
- Login endpoint: `/auth/login` (NOT `/api/auth/login`)
- Uses **params** not json for credentials
- Returns `token` field (not `access_token`)
- Authorization header: `Bearer {token}`

### Test Data Structure
```json
{
  "test_uuid": "generated-uuid-here",
  "test_date": "2026-01-04T19:30:00",
  "max_rpm": 6000,
  "max_current": 40,
  "gear_ratio": 1.0,
  "flywheel_inertia": 0.0256,
  "hardware_description": "Direct drive dyno",
  "avg_power_10a": 450.5,
  "avg_power_20a": 850.3,
  "avg_power_40a": 1500.8,
  "data_points": [
    {
      "timestamp": 0.02,
      "voltage": 12.5,
      "bus_voltage": 12.6,
      "current": 10.2,
      "rpm": 5800,
      "input_power": 127.5,
      "output_power": 120.3
    }
  ]
}
```

### Upload Button Logic
Enabled when:
- Test results exist (test has been run)
- Motor ID is selected
- Test has NOT been uploaded (checks local file and gets UUID)

Disabled when:
- No test data
- No motor selected
- Test already uploaded

---

## File Structure

```
motor-manager-2026/
├── backend/
│   └── app/
│       ├── main.py                    # FastAPI app
│       ├── database.py               # DB connection
│       ├── models/
│       │   └── __init__.py          # Pydantic models
│       ├── routers/
│       │   ├── auth.py              # Login endpoint
│       │   ├── motors.py            # Motor CRUD + tests
│       │   └── users.py             # User management
│       ├── static/
│       │   ├── js/auth-utils.js     # Token refresh
│       │   └── uploads/test_data/   # Compressed test files
│       └── templates/               # HTML pages
├── shared/
│   └── models/
│       └── models.py                # SQLAlchemy models
├── scripts/
│   ├── setup_db.py                  # Initial DB setup
│   └── migrate_*.py                 # Migration scripts
├── motor_test_app.py                # Windows test app
├── motor_test_controller.py         # Motor control logic
├── deploy.sh                        # Deployment script
├── docker-compose.yml               # Docker services
├── Dockerfile                       # App container
├── requirements.txt                 # Python dependencies
├── build_app.bat                    # Build single .exe
├── build_app_folder.bat             # Build folder-based exe
└── motor_icon.svg/ico               # App icon
```

---

## Next Steps / TODO

### High Priority
- [ ] Test duplicate prevention with actual hardware
- [ ] Verify folder-based .exe works with CANivore
- [ ] Add HTTPS to production deployment

### Medium Priority
- [ ] Add ability to delete individual tests
- [ ] Add data export for all motors
- [ ] Improve error handling in upload process
- [ ] Add test data validation before upload

### Low Priority
- [ ] Add motor comparison feature
- [ ] Create admin dashboard with statistics
- [ ] Add automated backups
- [ ] Improve mobile responsiveness

---

## Contact & Resources

**GitHub Repository:** https://github.com/VCHSRobots/motor-manager-2026  
**Team:** FRC Team 4415 - EPIC Robotz  
**School:** Valley Christian High School, Cerritos, CA

**External Dependencies:**
- CTRE Phoenix 6 (motor control)
- FastAPI (backend)
- PostgreSQL (database)
- Chart.js (graphing)
- Docker (deployment)

---

## Quick Reference Commands

**Local Development:**
```bash
python run_server.py
```

**Deploy to Droplet:**
```bash
ssh root@droplet_ip
cd motor-manager-2026
git pull origin main
./deploy.sh
```

**Build Windows App:**
```bash
build_app_folder.bat
```

**Run Migration Locally:**
```bash
python run_test_uuid_migration.py
```

**View Droplet Logs:**
```bash
docker-compose logs -f app
```

**Database Backup:**
```bash
docker-compose exec postgres pg_dump -U motor_user dynamometer_db > backup.sql
```

---

**Remember:** Always test locally before deploying to production!
