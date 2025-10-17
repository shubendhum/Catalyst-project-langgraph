# Deployment Guide for New Project

## Prerequisites

- Docker Desktop or Docker Engine installed
- Docker Compose installed
- Ports 3000, 8001, and 27017 available

## Quick Start

### 1. Build and Run

```bash
# Make deploy script executable
chmod +x deploy.sh

# Run deployment
./deploy.sh
```

### 2. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8001
- **API Documentation**: http://localhost:8001/docs
- **MongoDB**: mongodb://localhost:27017

### 3. View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f mongodb
```

### 4. Stop Services

```bash
docker-compose down

# Stop and remove volumes (CAUTION: deletes data)
docker-compose down -v
```

## Manual Deployment

### Build Images

```bash
docker-compose build
```

### Start Services

```bash
docker-compose up -d
```

### Check Status

```bash
docker-compose ps
```

## Production Deployment

### Environment Variables

1. Copy `.env.production` to `.env`
2. Update the following variables:
   - `JWT_SECRET_KEY`: Generate a secure random key
   - `MONGO_URL`: Update with production MongoDB URL
   - `REACT_APP_API_URL`: Update with production backend URL

### Security Checklist

- [ ] Change JWT_SECRET_KEY
- [ ] Use strong database passwords
- [ ] Enable HTTPS/TLS
- [ ] Configure firewall rules
- [ ] Set up database backups
- [ ] Enable monitoring and logging
- [ ] Review CORS settings
- [ ] Update default credentials

## Troubleshooting

### Container won't start

```bash
# Check logs
docker-compose logs [service-name]

# Rebuild container
docker-compose up --build [service-name]
```

### Port conflicts

Update port mappings in `docker-compose.yml`

### Database connection issues

Check MongoDB container is running:
```bash
docker-compose ps mongodb
```

## Health Checks

All services have health check endpoints:
- Frontend: http://localhost:3000/health
- Backend: http://localhost:8001/health
- MongoDB: Internal health check

## Scaling (Optional)

To run multiple instances:
```bash
docker-compose up --scale backend=3
```

## Backup Database

```bash
docker-compose exec mongodb mongodump --out=/backup
```

## Restore Database

```bash
docker-compose exec mongodb mongorestore /backup
```
