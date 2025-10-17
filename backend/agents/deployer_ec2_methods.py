"""
EC2 and EKS Deployment Methods for Deployer Agent
Contains all AWS deployment generation methods
"""
from typing import Dict, Optional


async def generate_ec2_user_data(self, project_name: str, architecture: Dict) -> str:
    """Generate EC2 user data script"""
    
    return f"""#!/bin/bash

# EC2 User Data Script for {project_name}

# Update system
yum update -y

# Install Docker
amazon-linux-extras install docker -y
systemctl start docker
systemctl enable docker
usermod -a -G docker ec2-user

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Create application directory
mkdir -p /app/{project_name}
cd /app/{project_name}

# Clone or copy application code
# Note: Replace this with your actual deployment method
# aws s3 sync s3://your-bucket/{project_name} .
# Or: git clone https://github.com/your-repo/{project_name}.git .

# Start application with Docker Compose
docker-compose up -d

# Configure logs
mkdir -p /var/log/{project_name}
docker-compose logs -f > /var/log/{project_name}/app.log 2>&1 &

echo "{project_name} deployment completed on EC2" >> /var/log/deployment.log
"""


async def generate_ec2_terraform(self, project_name: str, architecture: Dict, config: Dict) -> str:
    """Generate Terraform configuration for EC2"""
    
    instance_type = config.get("instance_type", "t3.medium")
    region = config.get("region", "us-east-1")
    key_name = config.get("key_name", "my-key-pair")
    
    return f"""# Terraform configuration for {project_name} on EC2

terraform {{
  required_version = ">= 1.0"
  required_providers {{
    aws = {{
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }}
  }}
}}

provider "aws" {{
  region = var.aws_region
}}

# VPC Configuration
resource "aws_vpc" "{project_name}_vpc" {{
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {{
    Name = "{project_name}-vpc"
  }}
}}

# Internet Gateway
resource "aws_internet_gateway" "{project_name}_igw" {{
  vpc_id = aws_vpc.{project_name}_vpc.id

  tags = {{
    Name = "{project_name}-igw"
  }}
}}

# Public Subnet
resource "aws_subnet" "{project_name}_public_subnet" {{
  vpc_id                  = aws_vpc.{project_name}_vpc.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = data.aws_availability_zones.available.names[0]
  map_public_ip_on_launch = true

  tags = {{
    Name = "{project_name}-public-subnet"
  }}
}}

# Route Table
resource "aws_route_table" "{project_name}_public_rt" {{
  vpc_id = aws_vpc.{project_name}_vpc.id

  route {{
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.{project_name}_igw.id
  }}

  tags = {{
    Name = "{project_name}-public-rt"
  }}
}}

resource "aws_route_table_association" "{project_name}_public_rta" {{
  subnet_id      = aws_subnet.{project_name}_public_subnet.id
  route_table_id = aws_route_table.{project_name}_public_rt.id
}}

# Security Group
resource "aws_security_group" "{project_name}_sg" {{
  name        = "{project_name}-sg"
  description = "Security group for {project_name}"
  vpc_id      = aws_vpc.{project_name}_vpc.id

  # HTTP
  ingress {{
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }}

  # HTTPS
  ingress {{
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }}

  # Frontend
  ingress {{
    from_port   = 3000
    to_port     = 3000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }}

  # Backend API
  ingress {{
    from_port   = 8001
    to_port     = 8001
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }}

  # SSH
  ingress {{
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = var.ssh_cidr_blocks
  }}

  # Outbound
  egress {{
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }}

  tags = {{
    Name = "{project_name}-sg"
  }}
}}

# EC2 Instance
resource "aws_instance" "{project_name}_ec2" {{
  ami           = data.aws_ami.amazon_linux_2.id
  instance_type = var.instance_type
  key_name      = var.key_name

  subnet_id              = aws_subnet.{project_name}_public_subnet.id
  vpc_security_group_ids = [aws_security_group.{project_name}_sg.id]

  user_data = file("${{path.module}}/../ec2-user-data.sh")

  root_block_device {{
    volume_size = 30
    volume_type = "gp3"
  }}

  tags = {{
    Name = "{project_name}-ec2"
  }}
}}

# Data sources
data "aws_availability_zones" "available" {{
  state = "available"
}}

data "aws_ami" "amazon_linux_2" {{
  most_recent = true
  owners      = ["amazon"]

  filter {{
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }}
}}

# Elastic IP
resource "aws_eip" "{project_name}_eip" {{
  instance = aws_instance.{project_name}_ec2.id
  domain   = "vpc"

  tags = {{
    Name = "{project_name}-eip"
  }}
}}
"""


def generate_terraform_variables(self, config: Dict) -> str:
    """Generate Terraform variables file"""
    
    return """variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.medium"
}

variable "key_name" {
  description = "SSH key pair name"
  type        = string
}

variable "ssh_cidr_blocks" {
  description = "CIDR blocks allowed for SSH access"
  type        = list(string)
  default     = ["0.0.0.0/0"]  # CHANGE THIS in production!
}

variable "project_name" {
  description = "Project name"
  type        = string
}
"""


def generate_terraform_outputs(self) -> str:
    """Generate Terraform outputs"""
    
    return """output "instance_id" {
  description = "EC2 instance ID"
  value       = aws_instance.*_ec2.id
}

output "public_ip" {
  description = "Public IP address"
  value       = aws_eip.*_eip.public_ip
}

output "public_dns" {
  description = "Public DNS name"
  value       = aws_instance.*_ec2.public_dns
}

output "frontend_url" {
  description = "Frontend URL"
  value       = "http://${aws_eip.*_eip.public_ip}:3000"
}

output "backend_url" {
  description = "Backend API URL"
  value       = "http://${aws_eip.*_eip.public_ip}:8001"
}
"""


async def generate_ec2_cloudformation(self, project_name: str, architecture: Dict, config: Dict) -> str:
    """Generate CloudFormation template for EC2"""
    
    return f"""AWSTemplateFormatVersion: '2010-09-09'
Description: CloudFormation template for {project_name} on EC2

Parameters:
  KeyName:
    Description: EC2 Key Pair for SSH access
    Type: AWS::EC2::KeyPair::KeyName
  
  InstanceType:
    Description: EC2 instance type
    Type: String
    Default: t3.medium
    AllowedValues:
      - t3.small
      - t3.medium
      - t3.large
      - t3.xlarge

Resources:
  VPC:
    Type: AWS::EC2::VPC
    Properties:
      CidrBlock: 10.0.0.0/16
      EnableDnsHostnames: true
      EnableDnsSupport: true
      Tags:
        - Key: Name
          Value: !Sub '${{AWS::StackName}}-vpc'

  InternetGateway:
    Type: AWS::EC2::InternetGateway
    Properties:
      Tags:
        - Key: Name
          Value: !Sub '${{AWS::StackName}}-igw'

  AttachGateway:
    Type: AWS::EC2::VPCGatewayAttachment
    Properties:
      VpcId: !Ref VPC
      InternetGatewayId: !Ref InternetGateway

  PublicSubnet:
    Type: AWS::EC2::Subnet
    Properties:
      VpcId: !Ref VPC
      CidrBlock: 10.0.1.0/24
      MapPublicIpOnLaunch: true
      AvailabilityZone: !Select [0, !GetAZs '']
      Tags:
        - Key: Name
          Value: !Sub '${{AWS::StackName}}-public-subnet'

  RouteTable:
    Type: AWS::EC2::RouteTable
    Properties:
      VpcId: !Ref VPC
      Tags:
        - Key: Name
          Value: !Sub '${{AWS::StackName}}-rt'

  Route:
    Type: AWS::EC2::Route
    DependsOn: AttachGateway
    Properties:
      RouteTableId: !Ref RouteTable
      DestinationCidrBlock: 0.0.0.0/0
      GatewayId: !Ref InternetGateway

  SubnetRouteTableAssociation:
    Type: AWS::EC2::SubnetRouteTableAssociation
    Properties:
      SubnetId: !Ref PublicSubnet
      RouteTableId: !Ref RouteTable

  SecurityGroup:
    Type: AWS::EC2::SecurityGroup
    Properties:
      GroupName: !Sub '${{AWS::StackName}}-sg'
      GroupDescription: Security group for {project_name}
      VpcId: !Ref VPC
      SecurityGroupIngress:
        - IpProtocol: tcp
          FromPort: 80
          ToPort: 80
          CidrIp: 0.0.0.0/0
        - IpProtocol: tcp
          FromPort: 443
          ToPort: 443
          CidrIp: 0.0.0.0/0
        - IpProtocol: tcp
          FromPort: 3000
          ToPort: 3000
          CidrIp: 0.0.0.0/0
        - IpProtocol: tcp
          FromPort: 8001
          ToPort: 8001
          CidrIp: 0.0.0.0/0
        - IpProtocol: tcp
          FromPort: 22
          ToPort: 22
          CidrIp: 0.0.0.0/0
      Tags:
        - Key: Name
          Value: !Sub '${{AWS::StackName}}-sg'

  EC2Instance:
    Type: AWS::EC2::Instance
    Properties:
      ImageId: !Sub '{{{{resolve:ssm:/aws/service/ami-amazon-linux-latest/amzn2-ami-hvm-x86_64-gp2}}}}'
      InstanceType: !Ref InstanceType
      KeyName: !Ref KeyName
      NetworkInterfaces:
        - AssociatePublicIpAddress: true
          DeviceIndex: '0'
          GroupSet:
            - !Ref SecurityGroup
          SubnetId: !Ref PublicSubnet
      UserData:
        Fn::Base64: !Sub |
          #!/bin/bash
          yum update -y
          amazon-linux-extras install docker -y
          systemctl start docker
          systemctl enable docker
          usermod -a -G docker ec2-user
          curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
          chmod +x /usr/local/bin/docker-compose
      Tags:
        - Key: Name
          Value: !Sub '${{AWS::StackName}}-ec2'

Outputs:
  InstanceId:
    Description: EC2 Instance ID
    Value: !Ref EC2Instance
  
  PublicIP:
    Description: Public IP address
    Value: !GetAtt EC2Instance.PublicIp
  
  PublicDNS:
    Description: Public DNS name
    Value: !GetAtt EC2Instance.PublicDnsName
  
  FrontendURL:
    Description: Frontend URL
    Value: !Sub 'http://${{EC2Instance.PublicIp}}:3000'
  
  BackendURL:
    Description: Backend API URL
    Value: !Sub 'http://${{EC2Instance.PublicIp}}:8001'
"""


def generate_ec2_deploy_script(self, project_name: str) -> str:
    """Generate EC2 deployment script"""
    
    return f"""#!/bin/bash

# EC2 Deployment Script for {project_name}

set -e

echo "🚀 Deploying {project_name} to EC2..."

# Check if Terraform is installed
if ! command -v terraform &> /dev/null; then
    echo "❌ Terraform is not installed. Please install it first."
    exit 1
fi

# Initialize Terraform
echo "📦 Initializing Terraform..."
cd terraform
terraform init

# Plan deployment
echo "📋 Planning deployment..."
terraform plan -out=tfplan

# Apply deployment
echo "🔄 Applying deployment..."
terraform apply tfplan

# Get outputs
echo "✅ Deployment complete!"
echo ""
terraform output

echo ""
echo "📝 Next steps:"
echo "1. SSH into the instance: ssh -i your-key.pem ec2-user@<PUBLIC_IP>"
echo "2. Check logs: sudo docker-compose logs -f"
echo "3. Access application:"
echo "   - Frontend: http://<PUBLIC_IP>:3000"
echo "   - Backend: http://<PUBLIC_IP>:8001"
"""


def generate_ec2_env(self, architecture: Dict) -> str:
    """Generate EC2 environment file"""
    
    return """# EC2 Environment Variables

# Backend
MONGO_URL=mongodb://mongodb:27017
DB_NAME=production_db
JWT_SECRET_KEY=CHANGE_THIS_IN_PRODUCTION
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
ENVIRONMENT=production

# Frontend  
# Note: Replace <PUBLIC_IP> with actual EC2 public IP
REACT_APP_API_URL=http://<PUBLIC_IP>:8001/api
REACT_APP_ENV=production

# AWS Configuration
AWS_REGION=us-east-1
AWS_DEFAULT_REGION=us-east-1
"""


async def generate_ec2_readme(self, project_name: str, config: Dict) -> str:
    """Generate EC2 deployment README"""
    
    return f"""# EC2 Deployment Guide for {project_name}

## Prerequisites

- AWS CLI configured with appropriate credentials
- Terraform installed (>= 1.0)
- OR CloudFormation access
- SSH key pair created in AWS
- Docker and Docker Compose (will be installed on EC2)

## Deployment Options

### Option 1: Terraform Deployment (Recommended)

1. **Configure variables**
```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values
```

2. **Deploy infrastructure**
```bash
./deploy-ec2.sh
```

3. **Access your application**
- Frontend: http://<PUBLIC_IP>:3000
- Backend: http://<PUBLIC_IP>:8001

### Option 2: CloudFormation Deployment

1. **Deploy stack**
```bash
aws cloudformation create-stack \\
  --stack-name {project_name} \\
  --template-body file://cloudformation/stack.yaml \\
  --parameters ParameterKey=KeyName,ParameterValue=your-key-pair \\
  --capabilities CAPABILITY_IAM
```

2. **Get outputs**
```bash
aws cloudformation describe-stacks \\
  --stack-name {project_name} \\
  --query 'Stacks[0].Outputs'
```

## Manual Deployment

If you prefer manual setup:

1. **Launch EC2 instance**
   - AMI: Amazon Linux 2
   - Instance Type: t3.medium or larger
   - Storage: 30GB
   - Security Group: Allow ports 22, 80, 443, 3000, 8001

2. **Connect to instance**
```bash
ssh -i your-key.pem ec2-user@<PUBLIC_IP>
```

3. **Run user data script**
```bash
sudo bash /path/to/ec2-user-data.sh
```

4. **Deploy application**
```bash
cd /app/{project_name}
# Upload your code here
docker-compose up -d
```

## Post-Deployment

### Update Environment Variables

```bash
ssh -i your-key.pem ec2-user@<PUBLIC_IP>
cd /app/{project_name}
nano .env.production
# Update PUBLIC_IP and other variables
docker-compose restart
```

### Monitor Application

```bash
# View logs
docker-compose logs -f

# Check service status
docker-compose ps

# View system resources
htop
```

### Set Up Domain (Optional)

1. Create A record pointing to EC2 public IP
2. Update REACT_APP_API_URL in .env
3. Configure SSL with Let's Encrypt

## Scaling

For production workloads, consider:
- Auto Scaling Group
- Application Load Balancer
- RDS for MongoDB
- ElastiCache for caching
- CloudFront CDN

## Cost Optimization

- Use Reserved Instances for long-term savings
- Stop instances during non-business hours
- Monitor with AWS Cost Explorer
- Use Savings Plans

## Troubleshooting

### Instance not accessible
- Check Security Group rules
- Verify instance is running
- Check system logs in AWS Console

### Application not starting
- SSH into instance and check Docker logs
- Verify docker-compose.yml is correct
- Check disk space: `df -h`

### Performance issues
- Upgrade instance type
- Add more memory
- Optimize Docker images
"""
