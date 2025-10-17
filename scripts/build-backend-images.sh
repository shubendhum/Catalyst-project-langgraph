# Build all backend Docker images

echo "Building Catalyst Backend Docker Images..."
echo ""

# Build production image
echo "1. Building Production Image (Debian-based)..."
docker build \
  -f Dockerfile.backend.prod \
  -t catalyst-backend:latest \
  -t catalyst-backend:1.0.0 \
  -t catalyst-backend:production \
  .

echo "✓ Production image built successfully"
echo ""

# Build development image
echo "2. Building Development Image..."
docker build \
  -f Dockerfile.backend.dev \
  -t catalyst-backend:dev \
  -t catalyst-backend:development \
  .

echo "✓ Development image built successfully"
echo ""  

# Build minimal Alpine image
echo "3. Building Minimal Image (Alpine-based)..."
docker build \
  -f Dockerfile.backend.alpine \
  -t catalyst-backend:alpine \
  -t catalyst-backend:minimal \
  .

echo "✓ Minimal image built successfully"
echo ""

# Show built images
echo "============================================"
echo "Built Images:"
echo "============================================"
docker images | grep catalyst-backend

echo ""
echo "Image sizes:"
docker images catalyst-backend --format "{{.Repository}}:{{.Tag}} - {{.Size}}"

echo ""
echo "✓ All backend images built successfully!"