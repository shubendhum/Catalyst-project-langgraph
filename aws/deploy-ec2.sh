#!/bin/bash
# EC2 deployment script

set -e

echo "🚀 Catalyst EC2 Deployment Script"
echo "==================================="

# Configuration
REGION="us-east-1"
INSTANCE_TYPE="t3.medium"
KEY_NAME="your-key-pair"
SECURITY_GROUP="catalyst-sg"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

function print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

function print_error() {
    echo -e "${RED}✗ $1${NC}"
}

function print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# Check AWS CLI
if ! command -v aws &> /dev/null; then
    print_error "AWS CLI not found. Please install it first."
    exit 1
fi

print_success "AWS CLI found"

# Create security group
print_info "Creating security group..."
SG_ID=$(aws ec2 create-security-group \
    --group-name $SECURITY_GROUP \
    --description "Security group for Catalyst" \
    --region $REGION \
    --output text 2>/dev/null || echo "exists")

if [ "$SG_ID" != "exists" ]; then
    print_success "Security group created: $SG_ID"
    
    # Add inbound rules
    aws ec2 authorize-security-group-ingress \
        --group-name $SECURITY_GROUP \
        --protocol tcp --port 22 --cidr 0.0.0.0/0 \
        --region $REGION
    
    aws ec2 authorize-security-group-ingress \
        --group-name $SECURITY_GROUP \
        --protocol tcp --port 80 --cidr 0.0.0.0/0 \
        --region $REGION
    
    aws ec2 authorize-security-group-ingress \
        --group-name $SECURITY_GROUP \
        --protocol tcp --port 443 --cidr 0.0.0.0/0 \
        --region $REGION
    
    aws ec2 authorize-security-group-ingress \
        --group-name $SECURITY_GROUP \
        --protocol tcp --port 3000 --cidr 0.0.0.0/0 \
        --region $REGION
    
    aws ec2 authorize-security-group-ingress \
        --group-name $SECURITY_GROUP \
        --protocol tcp --port 8001 --cidr 0.0.0.0/0 \
        --region $REGION
    
    print_success "Security group rules configured"
else
    print_info "Security group already exists"
fi

# Get latest Ubuntu AMI
print_info "Finding latest Ubuntu AMI..."
AMI_ID=$(aws ec2 describe-images \
    --owners 099720109477 \
    --filters "Name=name,Values=ubuntu/images/hvm-ssd/ubuntu-focal-20.04-amd64-server-*" \
    --query 'sort_by(Images, &CreationDate)[-1].ImageId' \
    --region $REGION \
    --output text)

print_success "Found AMI: $AMI_ID"

# Create user data script
cat > user-data.sh << 'EOF'
#!/bin/bash
set -e

# Update system
apt-get update
apt-get upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
usermod -aG docker ubuntu

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Install Git
apt-get install -y git

# Clone repository (replace with your repo)
# cd /home/ubuntu
# git clone <your-repo-url> catalyst
# cd catalyst
# docker-compose -f docker-compose.prod.yml up -d

echo "Setup complete!"
EOF

# Launch EC2 instance
print_info "Launching EC2 instance..."
INSTANCE_ID=$(aws ec2 run-instances \
    --image-id $AMI_ID \
    --instance-type $INSTANCE_TYPE \
    --key-name $KEY_NAME \
    --security-groups $SECURITY_GROUP \
    --user-data file://user-data.sh \
    --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=Catalyst-Server}]" \
    --region $REGION \
    --query 'Instances[0].InstanceId' \
    --output text)

if [ -z "$INSTANCE_ID" ]; then
    print_error "Failed to launch instance"
    exit 1
fi

print_success "Instance launched: $INSTANCE_ID"

# Wait for instance to be running
print_info "Waiting for instance to be running..."
aws ec2 wait instance-running --instance-ids $INSTANCE_ID --region $REGION
print_success "Instance is running"

# Get public IP
PUBLIC_IP=$(aws ec2 describe-instances \
    --instance-ids $INSTANCE_ID \
    --region $REGION \
    --query 'Reservations[0].Instances[0].PublicIpAddress' \
    --output text)

print_success "Instance deployed successfully!"
echo ""
echo "==================================="
echo "Instance ID: $INSTANCE_ID"
echo "Public IP: $PUBLIC_IP"
echo "SSH Command: ssh -i $KEY_NAME.pem ubuntu@$PUBLIC_IP"
echo "==================================="
echo ""
print_info "Wait a few minutes for Docker installation to complete, then:"
echo "1. SSH into the instance"
echo "2. Clone your repository"
echo "3. Run: docker-compose -f docker-compose.prod.yml up -d"
echo "4. Access: http://$PUBLIC_IP:3000"

# Cleanup
rm -f user-data.sh
