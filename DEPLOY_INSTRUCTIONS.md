# Deployment Instructions for DigitalOcean Droplet

## Pre-Deployment Checklist

### 1. Commit and Push All Changes
```bash
# In your local Windows machine (PowerShell)
cd C:\Users\dalbr\Documents\Projects\Epic_Robots_2026\Dynamometer

# Check status
git status

# Add all changes
git add .

# Commit with message
git commit -m "Add test UUID duplicate prevention and UI improvements"

# Push to GitHub
git push origin main
```

### 2. Verify Droplet Information
You'll need:
- **Droplet IP Address**: `YOUR_DROPLET_IP`
- **SSH Access**: `ssh root@YOUR_DROPLET_IP`

---

## Deployment Steps

### Step 1: SSH into Your Droplet
```bash
ssh root@YOUR_DROPLET_IP
```

### Step 2: Navigate to Project (or clone if first time)

**If first deployment:**
```bash
# Clone the repository
git clone https://github.com/VCHSRobots/motor-manager-2026.git
cd motor-manager-2026
```

**If updating existing installation:**
```bash
# Navigate to existing directory
cd motor-manager-2026
```

### Step 3: Create/Update Environment File
```bash
nano .env
```

Add these variables (customize the passwords):
```env
# Database connection for Docker
DATABASE_URL=postgresql://motor_user:CHOOSE_DB_PASSWORD@postgres:5432/dynamometer_db

# Postgres password (must match DATABASE_URL)
POSTGRES_PASSWORD=CHOOSE_DB_PASSWORD

# Admin login password
ADMIN_PASSWORD=CHOOSE_ADMIN_PASSWORD

# Standard user login password
USER_PASSWORD=CHOOSE_USER_PASSWORD

# Default admin username (optional, defaults to 'admin')
DEFAULT_ADMIN_USERNAME=admin
```

**Important:** 
- Replace `CHOOSE_DB_PASSWORD` with a strong password (use same in both places)
- Replace `CHOOSE_ADMIN_PASSWORD` with your desired admin login password
- Replace `CHOOSE_USER_PASSWORD` with your desired standard user login password

Save and exit: `Ctrl+X`, then `Y`, then `Enter`

### Step 4: Make Deploy Script Executable
```bash
chmod +x deploy.sh
```

### Step 5: Run Deployment
```bash
./deploy.sh
```

When prompted "Continue? (yes/no):", type `yes` and press Enter.

**This will:**
- Pull latest code from GitHub
- Stop and remove existing containers and volumes (⚠️ **deletes all data**)
- Build fresh Docker images
- Start all services with a clean database
- Run all migrations (including the new test_uuid migration)

**Expected output:**
```
🚀 Starting deployment update...
⚠️  WARNING: This will delete all existing motor data!

Continue? (yes/no): yes
📥 Pulling latest code from GitHub...
🛑 Stopping existing services...
🏗️ Building Docker images...
🚀 Starting services...
⏳ Waiting for database to initialize...
🔄 Running database migrations...
✅ Deployment complete!
```

### Step 6: Verify Deployment
```bash
# Check that containers are running
docker-compose ps

# You should see:
# - dynamometer-app-1 (running)
# - dynamometer-postgres-1 (running)

# Check logs for any errors
docker-compose logs -f
```

Press `Ctrl+C` to exit logs.

### Step 7: Access Your Application
Open your browser and navigate to:
```
http://YOUR_DROPLET_IP
```

**Login credentials:**
- Username: `admin`
- Password: `[whatever you set as ADMIN_PASSWORD]`

---

## What's New in This Deployment

### 1. Test UUID Duplicate Prevention
- Each test now has a unique UUID
- Tests cannot be uploaded twice (client-side and server-side validation)
- Upload button is disabled after successful upload
- Tracked locally in `uploaded_tests.json`

### 2. UI Improvements
- Motor detail page is more compact
- Motor picture integrated into top section (smaller, 200x200px)
- Average power metrics inline with status
- Test selection more compact
- Graph visible "above the fold"

### 3. Database Changes
- New `test_uuid` column in `performance_tests` table
- Unique constraint on test_uuid prevents database-level duplicates

---

## Post-Deployment Tasks

### Create Additional Users (Optional)
1. Log in as admin
2. Click "Setup" button
3. Add users as needed

### Upload Motor Data
You can now add motors and upload test data from the Windows dynamometer app!

---

## Troubleshooting

### Check Application Logs
```bash
docker-compose logs -f app
```

### Check Database Logs
```bash
docker-compose logs -f postgres
```

### Restart Services
```bash
docker-compose restart
```

### Complete Reset (⚠️ Deletes All Data)
```bash
docker-compose down -v
docker-compose up -d
```

### Enter Application Container
```bash
docker-compose exec app bash
```

### Check Database Connection
```bash
docker-compose exec app python -c "from backend.app.database import engine; print('Connected!' if engine else 'Failed')"
```

---

## Backup Before Future Updates

To backup your database before future deployments:
```bash
docker-compose exec postgres pg_dump -U motor_user dynamometer_db > backup_$(date +%Y%m%d_%H%M%S).sql
```

To restore from backup:
```bash
cat backup_YYYYMMDD_HHMMSS.sql | docker-compose exec -T postgres psql -U motor_user dynamometer_db
```

---

## Useful Commands

### View All Containers
```bash
docker ps -a
```

### View Container Resource Usage
```bash
docker stats
```

### Stop Application
```bash
docker-compose down
```

### Start Application
```bash
docker-compose up -d
```

### Pull Latest Code and Rebuild
```bash
git pull origin main
docker-compose build
docker-compose up -d
```

### View Nginx-style Access Logs
```bash
docker-compose logs -f app | grep "GET\|POST\|PUT\|DELETE"
```

---

## Security Notes

1. **Change Default Passwords**: Make sure to use strong, unique passwords in your `.env` file
2. **Firewall**: Consider setting up UFW firewall to only allow ports 22 (SSH) and 80 (HTTP)
3. **HTTPS**: For production, consider adding SSL/TLS with Let's Encrypt
4. **SSH Keys**: Use SSH key authentication instead of passwords for better security

---

## Need Help?

If deployment fails:
1. Check the error messages in the terminal
2. View logs: `docker-compose logs -f`
3. Verify `.env` file has correct values
4. Ensure GitHub repository is accessible from droplet
5. Check Docker is running: `docker --version`

---

**Last Updated:** January 4, 2026
**Version:** 2.0 (with UUID duplicate prevention)
