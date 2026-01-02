#!/bin/bash

# Deployment script for Motor Manager 2026
# Run this on your DigitalOcean droplet

set -e  # Exit on any error

echo "🚀 Starting deployment..."

# Update system
echo "📦 Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y

# Install Docker if not already installed
if ! command -v docker &> /dev/null; then
    echo "🐳 Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    rm get-docker.sh
fi

# Install Docker Compose if not already installed
if ! command -v docker-compose &> /dev/null; then
    echo "🐳 Installing Docker Compose..."
    sudo apt-get install -y docker-compose
fi

# Pull latest code
echo "📥 Pulling latest code..."
git pull origin main

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "⚙️ Creating .env file..."
    cp .env.example .env
    echo ""
    echo "⚠️  IMPORTANT: Edit .env file with your secure passwords:"
    echo "   nano .env"
    echo ""
    read -p "Press Enter after you've edited the .env file..."
fi

# Build and start containers
echo "🏗️ Building Docker images..."
docker-compose build

echo "🚀 Starting services..."
docker-compose down
docker-compose up -d

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
sleep 10

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
echo "🌐 Your application should be available at:"
echo "   http://$(curl -s ifconfig.me)"
echo ""
echo "📝 Useful commands:"
echo "   View logs:        docker-compose logs -f"
echo "   Restart:          docker-compose restart"
echo "   Stop:             docker-compose down"
echo "   Start:            docker-compose up -d"
echo "   Enter container:  docker-compose exec app bash"
echo ""
