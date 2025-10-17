#!/bin/bash

# Deployment script for New Project

echo "🚀 Starting deployment..."

# Build and start containers
echo "📦 Building Docker images..."
docker-compose build

echo "🔄 Starting services..."
docker-compose up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be healthy..."
sleep 10

# Check service health
echo "🏥 Checking service health..."
docker-compose ps

# Run database migrations if needed
# docker-compose exec backend python migrate.py

echo "✅ Deployment complete!"
echo ""
echo "Services running:"
echo "  Frontend: http://localhost:3000"
echo "  Backend API: http://localhost:8001"
echo "  MongoDB: mongodb://localhost:27017"
echo ""
echo "To view logs: docker-compose logs -f"
echo "To stop: docker-compose down"
