# Quick Update Deployment for DigitalOcean Droplet

## Updating Existing Installation (Fresh Start - No Data Preserved)

### Step 1: SSH into your droplet
```bash
ssh root@YOUR_DROPLET_IP
```

### Step 2: Navigate to the project directory
```bash
cd motor-manager-2026
```

### Step 3: Run the update deployment
```bash
./deploy.sh
```

When prompted, type `yes` to confirm. This will:
- Pull the latest code from GitHub
- Stop existing containers
- **Delete all existing data** (motors, logs, performance tests)
- Build fresh Docker images
- Start services with a clean database

### Step 4: Access your application
Open in browser: `http://YOUR_DROPLET_IP`

Login with:
- Username: `admin`
- Password: (the ADMIN_PASSWORD from your existing .env file)

---

## Useful Commands After Deployment

### View logs
```bash
docker-compose logs -f
```

### Restart application
```bash
docker-compose restart
```

### Stop application
```bash
docker-compose down
```

### Start application
```bash
docker-compose up -d
```

### Update to latest code
```bash
git pull origin main
docker-compose build
docker-compose up -d
```

### Backup database
```bash
docker-compose exec postgres pg_dump -U motor_user dynamometer_db > backup_$(date +%Y%m%d).sql
```

---

## Troubleshooting

If something goes wrong:

1. Check logs: `docker-compose logs -f`
2. Check container status: `docker-compose ps`
3. Restart services: `docker-compose restart`
4. Reset everything (⚠️ deletes data): `docker-compose down -v && docker-compose up -d`
