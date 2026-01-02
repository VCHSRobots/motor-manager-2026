# Motor Manager 2026 - Deployment Guide

## Prerequisites

- DigitalOcean Droplet (Ubuntu 22.04 or later recommended)
- Domain name (optional, but recommended)
- SSH access to your droplet

## Quick Deployment Steps

### 1. Initial Droplet Setup

SSH into your droplet:
```bash
ssh root@your_droplet_ip
```

### 2. Clone Repository

```bash
# Install git if not already installed
apt-get update
apt-get install -y git

# Clone your repository
git clone https://github.com/VCHSRobots/motor-manager-2026.git
cd motor-manager-2026
```

### 3. Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit with your secure passwords
nano .env
```

**Important:** Set strong passwords for:
- `ADMIN_PASSWORD` - Admin access password
- `USER_PASSWORD` - Regular user password  
- `POSTGRES_PASSWORD` - Database password
- `DATABASE_URL` - Should be: `postgresql://motor_user:YOUR_POSTGRES_PASSWORD@postgres:5432/dynamometer_db`

### 4. Run Deployment Script

```bash
# Make the script executable
chmod +x deploy.sh

# Run deployment
./deploy.sh
```

The script will:
- Install Docker and Docker Compose
- Build the application containers
- Start PostgreSQL database
- Run database migrations
- Start the FastAPI application

### 5. Access Your Application

Open your browser and navigate to:
```
http://your_droplet_ip
```

Default login:
- Username: `admin`
- Password: (the ADMIN_PASSWORD you set in .env)

## Manual Deployment (Alternative)

If you prefer manual control:

```bash
# Build containers
docker-compose build

# Start services
docker-compose up -d

# Check logs
docker-compose logs -f

# Run migrations
docker-compose exec app python scripts/migrate_role_protected.py
docker-compose exec app python scripts/migrate_name_optional.py
```

## Post-Deployment

### Set Up Domain (Optional)

1. Point your domain A record to your droplet IP
2. Install nginx for HTTPS:

```bash
sudo apt-get install -y nginx certbot python3-certbot-nginx

# Create nginx config
sudo nano /etc/nginx/sites-available/motor-manager
```

Example nginx config:
```nginx
server {
    listen 80;
    server_name your_domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable and get SSL:
```bash
sudo ln -s /etc/nginx/sites-available/motor-manager /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
sudo certbot --nginx -d your_domain.com
```

### Firewall Configuration

```bash
# Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow 22/tcp  # SSH
sudo ufw enable
```

## Maintenance

### View Logs
```bash
docker-compose logs -f app      # Application logs
docker-compose logs -f postgres # Database logs
```

### Restart Services
```bash
docker-compose restart
```

### Update Application
```bash
git pull origin main
docker-compose build
docker-compose up -d
```

### Backup Database
```bash
docker-compose exec postgres pg_dump -U motor_user dynamometer_db > backup_$(date +%Y%m%d).sql
```

### Restore Database
```bash
cat backup_20260102.sql | docker-compose exec -T postgres psql -U motor_user dynamometer_db
```

## Troubleshooting

### Check Container Status
```bash
docker-compose ps
```

### Enter Container Shell
```bash
docker-compose exec app bash
```

### Reset Everything
```bash
docker-compose down -v  # WARNING: Deletes database!
docker-compose up -d
```

### Check Database Connection
```bash
docker-compose exec app python -c "from shared.models.database import engine; print(engine.connect())"
```

## Security Notes

1. **Never commit .env file** to version control
2. **Use strong passwords** for all credentials
3. **Enable firewall** (ufw) on your droplet
4. **Use HTTPS** in production with Let's Encrypt
5. **Regular backups** of the database
6. **Keep system updated**: `apt-get update && apt-get upgrade`

## Support

For issues or questions:
- Check logs: `docker-compose logs -f`
- Review GitHub Issues
- Contact team admin

---

**FRC Team 4415 - Epic Robots**  
Valley Christian High School, Cerritos, CA
