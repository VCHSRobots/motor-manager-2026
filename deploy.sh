#!/bin/bash

# Update deployment script for Motor Manager 2026
# Run this on your DigitalOcean droplet when updating to a new version
# WARNING: This will delete all existing data!

set -e  # Exit on any error

echo "🚀 Starting deployment update..."
echo "⚠️  WARNING: This will delete all existing motor data!"
echo ""
read -p "Continue? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "Deployment cancelled."
    exit 1
fi

# Pull latest code
echo "📥 Pulling latest code from GitHub..."
git pull origin main

# Stop and remove existing containers and volumes
echo "🛑 Stopping existing services..."
docker-compose down -v

# Build new images
echo "🏗️ Building Docker images..."
docker-compose build --no-cache

# Start services with fresh database
echo "🚀 Starting services..."
docker-compose up -d

# Wait for database to be ready
echo "⏳ Waiting for database to initialize..."
sleep 15

# Run migrations
echo "🔄 Running database migrations..."
docker-compose exec -T app python scripts/migrate_role_protected.py || true
docker-compose exec -T app python scripts/migrate_name_optional.py || true

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📊 Service status:"
docker-compose ps
echo ""
echo "🌐 Your application is available at:"
echo "   http://$(curl -s ifconfig.me)"
echo ""
echo "🔑 Login credentials:"
echo "   Username: admin"
echo "   Password: (from your .env file ADMIN_PASSWORD)"
echo ""
echo "📝 Useful commands:"
echo "   View logs:        docker-compose logs -f"
echo "   Restart:          docker-compose restart"
echo "   Enter container:  docker-compose exec app bash"
echo ""
