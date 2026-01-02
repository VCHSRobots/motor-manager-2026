# Website Redesign - Setup Instructions

## Overview
The website has been completely redesigned with:
- 🎨 Light pink theme throughout
- 🏠 New landing page explaining the system
- 🔐 Improved authentication flow
- 📊 Comprehensive motor management with all parameters
- 📝 Motor log entries with dates
- 📸 Picture upload capability
- 📈 Performance data tracking
- 🔢 Auto-generated Motor IDs (yyyy-nnn format)

## Database Migration

**IMPORTANT:** You must run the migration script to update your database schema before running the server.

```powershell
$env:DATABASE_URL = "postgresql://postgres:puck@localhost:5432/dynamometer_db"
python scripts/migrate_motor_schema.py
```

This will:
- Add all new motor fields (motor_id, motor_type, purchase info, peak power measurements, etc.)
- Create the motor_logs table for log entries
- Create the performance_tests table for test data
- Update existing motors with default status "On Order"

## Install New Dependencies

```powershell
pip install python-multipart pillow
```

Or reinstall from requirements.txt:

```powershell
pip install -r requirements.txt
```

## Start the Server

```powershell
python run_server.py
```

## Page Structure

### Landing Page (/)
- Displays when user is not logged in
- Explains what the system is for
- Shows owner information (EPIC Robotz Team)
- Single "Login" button
- Auto-redirects to /motors if already logged in

### Login Page (/login-page)
- Username and password form
- Supports both ADMIN_PASSWORD and USER_PASSWORD
- Stores auth token and role in localStorage
- Redirects admin to /motors, user to /motors

### Main Motors Page (/motors)
- Lists all motors in a table
- Sortable by: Motor ID, Name, Date of Purchase, Status, Peak Powers
- Shows key metrics for each motor
- Click any motor row to view details
- "Add Motor" button to create new motor

### Motor Detail Page (/motor/{id})
- Shows all motor parameters
- Key metrics displayed prominently (Peak Power at 20A, 30A, 40A)
- Motor picture with upload capability
- Performance test graph (Chart.js)
- Motor log entries (dated, by user)
- Add new log entries
- Edit motor (button - functionality to be implemented)
- Delete motor (admin only)

### User Management (/manage-users)
- Admin only
- Create/delete users
- Assign roles (admin/user)

## Motor ID System

Motors get their ID assigned automatically when you:
1. Fill out Name, Type, and Date of Purchase (or Season/Year)
2. Click "Create Motor"

The ID format is `yyyy-nnn` where:
- `yyyy` = year the ID was created
- `nnn` = sequence number (001, 002, etc.)

Example: `2026-001`, `2026-002`, etc.

Once assigned, the Motor ID **never changes** and is **never reused** even if the motor is deleted.

## Motor Status Options

- **On Order** - Motor has been ordered but not received
- **Available** - Motor is in inventory and ready to use
- **In Service** - Motor is currently being used
- **Retired** - Motor is no longer in active use
- **Damaged** - Motor is damaged and needs repair/replacement

## Date of Purchase

Two options:
1. **Exact Date**: Use the date picker (mm/dd/yyyy)
2. **Season/Year**: Select from dropdown (Winter, Spring, Summer, Fall) + enter year

## Peak Power Measurements

The system tracks peak power output at 4 different amperage levels:
- 10A
- 20A
- 30A
- 40A

These are automatically updated from the latest performance test.

## Motor Log

- Each motor has a log for notes and updates
- Every entry is automatically dated and attributed to the user who created it
- Displayed in reverse chronological order (newest first)

## File Uploads

### Motor Pictures
- Supported formats: JPEG, PNG, GIF, WebP
- Stored in `backend/app/static/uploads/motors/`
- Named by motor ID
- Displayed on motor detail page

### Performance Data
- Coming soon: Upload CSV files from Windows test program
- Will parse and store test data
- Auto-generates graphs
- Updates peak power measurements

## API Endpoints

### Motors
- `GET /motors` - List all motors
- `POST /motors` - Create new motor
- `GET /motors/{id}` - Get motor details
- `PUT /motors/{id}` - Update motor
- `DELETE /motors/{id}` - Delete motor (admin only)

### Motor Logs
- `GET /motors/{id}/logs` - Get motor log entries
- `POST /motors/{id}/logs` - Add log entry

### File Upload
- `POST /motors/{id}/upload-picture` - Upload motor picture

## Header (All Pages Except Landing)

Every page shows:
- Title: "EPIC Robotz Motor Management System"
- Username display
- Setup button (admin only) → links to /manage-users
- Logout button

## Styling

- Background: Light pink (#ffe4e9)
- Primary gradient: Pink to deep rose (#ff6b9d → #c44569)
- Cards: White with rounded corners and shadows
- Buttons: Consistent styling with hover effects
- Tables: Pink-themed headers with hover states
- Status badges: Color-coded by status type

## Next Steps

1. ✅ Run database migration
2. ✅ Install dependencies
3. ✅ Start server
4. ✅ Login at http://localhost:8000/
5. Test creating a motor
6. Test uploading a picture
7. Test adding log entries
8. Test sorting motors

## Future Enhancements

- [ ] Edit motor functionality
- [ ] Performance data CSV upload
- [ ] Parse and store test data (time-series)
- [ ] Interactive performance graphs from actual data
- [ ] Export functionality
- [ ] Search/filter motors
- [ ] Bulk operations
- [ ] Email notifications
- [ ] PDF reports

## Notes

- The old "description" field has been removed
- Comments and Runs tables still exist but aren't actively used in the new UI
- Motor deletion cascades to logs and performance tests
- File uploads are stored locally (consider DigitalOcean Spaces for production)
