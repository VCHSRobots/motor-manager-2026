# Deployment Guide for DigitalOcean Droplet

Follow these steps to deploy the latest version of the Motor Manager server to your DigitalOcean droplet.

## 1. Connect to your Droplet
Open a terminal (or PowerShell) and SSH into your server:
```bash
ssh root@your_droplet_ip_address
```

## 2. Navigate to the Project Directory
Go to the folder where the project is cloned (e.g., `/opt/motor-manager` or `~/motor-manager-2026`). If you are unsure, list directories with `ls`.
```bash
cd path/to/motor-manager-2026
```

## 3. Get the Latest Code
Pull the changes you just pushed to GitHub.
```bash
git pull origin main
```
*(If you have local changes on the server that prevent pulling, you can force it with `git reset --hard origin/main` since you don't care about server-side changes)*

## 4. Update Configuration (.env)
Ensure your `.env` file has the secure passwords.
```bash
nano .env
```
Make sure it looks like this (generate your own secure passwords):
```ini
POSTGRES_PASSWORD=secure_db_password
DATABASE_URL=postgresql://motor_user:secure_db_password@postgres:5432/dynamometer_db
ADMIN_PASSWORD=loveepic
USER_PASSWORD=epic4fun
DEFAULT_ADMIN_USERNAME=admin
```
*(Press `Ctrl+X`, then `Y`, then `Enter` to save)*

## 5. Deploy & Reset Data
Since you want to start fresh and wipe existing data:

1. Stop containers and **delete volumes** (wipes the database):
   ```bash
   docker-compose down -v
   ```

2. Rebuild and start the server:
   ```bash
   docker-compose up -d --build
   ```

## 6. Verify
Check that the containers are running:
```bash
docker-compose ps
```

You can view logs if something goes wrong:
```bash
docker-compose logs -f
```

The server should now be live at `http://your_droplet_ip_address`.
