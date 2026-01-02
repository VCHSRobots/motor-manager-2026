# Quick Deployment Commands for DigitalOcean Droplet

## Step 1: SSH into your droplet
```bash
ssh root@YOUR_DROPLET_IP
```

## Step 2: Clone the repository
```bash
apt-get update
apt-get install -y git
git clone https://github.com/VCHSRobots/motor-manager-2026.git
cd motor-manager-2026
```

## Step 3: Configure environment variables
```bash
cp .env.example .env
nano .env
```

**Edit these values in .env:**
```
DATABASE_URL=postgresql://motor_user:YOUR_STRONG_DB_PASSWORD@postgres:5432/dynamometer_db
ADMIN_PASSWORD=your_strong_admin_password
USER_PASSWORD=your_strong_user_password
POSTGRES_PASSWORD=YOUR_STRONG_DB_PASSWORD
```

Press `Ctrl+X`, then `Y`, then `Enter` to save.

## Step 4: Run the deployment script
```bash
chmod +x deploy.sh
./deploy.sh
```

## Step 5: Access your application
Open in browser: `http://YOUR_DROPLET_IP`

Login with:
- Username: `admin`
- Password: (the ADMIN_PASSWORD from .env)

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
