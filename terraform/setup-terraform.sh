#!/bin/bash

# Terraform Setup Script for TradeSense Infrastructure
# This script initializes Terraform and sets up the backend

set -e

# Configuration
AWS_REGION=${AWS_REGION:-us-east-1}
PROJECT_NAME="tradesense"
ENVIRONMENT=${1:-production}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check Terraform
    if ! command -v terraform &> /dev/null; then
        error "Terraform is not installed!"
        echo "Install from: https://www.terraform.io/downloads.html"
        exit 1
    fi
    
    # Check AWS CLI
    if ! command -v aws &> /dev/null; then
        error "AWS CLI is not installed!"
        echo "Install from: https://aws.amazon.com/cli/"
        exit 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity &> /dev/null; then
        error "AWS credentials not configured!"
        echo "Run: aws configure"
        exit 1
    fi
    
    success "Prerequisites check passed"
}

# Create S3 backend bucket
create_backend_bucket() {
    log "Creating S3 backend bucket..."
    
    BUCKET_NAME="${PROJECT_NAME}-terraform-state"
    
    # Check if bucket exists
    if aws s3api head-bucket --bucket "$BUCKET_NAME" 2>/dev/null; then
        warning "S3 bucket $BUCKET_NAME already exists"
    else
        # Create bucket
        if [[ "$AWS_REGION" == "us-east-1" ]]; then
            aws s3api create-bucket \
                --bucket "$BUCKET_NAME" \
                --region "$AWS_REGION"
        else
            aws s3api create-bucket \
                --bucket "$BUCKET_NAME" \
                --region "$AWS_REGION" \
                --create-bucket-configuration LocationConstraint="$AWS_REGION"
        fi
        
        # Enable versioning
        aws s3api put-bucket-versioning \
            --bucket "$BUCKET_NAME" \
            --versioning-configuration Status=Enabled
        
        # Enable encryption
        aws s3api put-bucket-encryption \
            --bucket "$BUCKET_NAME" \
            --server-side-encryption-configuration '{
                "Rules": [{
                    "ApplyServerSideEncryptionByDefault": {
                        "SSEAlgorithm": "AES256"
                    }
                }]
            }'
        
        # Block public access
        aws s3api put-public-access-block \
            --bucket "$BUCKET_NAME" \
            --public-access-block-configuration \
                "BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true"
        
        success "S3 bucket created: $BUCKET_NAME"
    fi
}

# Create DynamoDB table for state locking
create_lock_table() {
    log "Creating DynamoDB table for state locking..."
    
    TABLE_NAME="${PROJECT_NAME}-terraform-locks"
    
    # Check if table exists
    if aws dynamodb describe-table --table-name "$TABLE_NAME" &>/dev/null; then
        warning "DynamoDB table $TABLE_NAME already exists"
    else
        # Create table
        aws dynamodb create-table \
            --table-name "$TABLE_NAME" \
            --attribute-definitions AttributeName=LockID,AttributeType=S \
            --key-schema AttributeName=LockID,KeyType=HASH \
            --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5 \
            --region "$AWS_REGION"
        
        # Wait for table to be active
        log "Waiting for table to be active..."
        aws dynamodb wait table-exists --table-name "$TABLE_NAME"
        
        success "DynamoDB table created: $TABLE_NAME"
    fi
}

# Create terraform.tfvars file
create_tfvars() {
    log "Creating terraform.tfvars file..."
    
    if [[ -f "terraform.tfvars" ]]; then
        warning "terraform.tfvars already exists. Creating backup..."
        cp terraform.tfvars "terraform.tfvars.backup.$(date +%Y%m%d_%H%M%S)"
    fi
    
    # Get user email
    read -p "Enter owner email address: " OWNER_EMAIL
    
    # Create tfvars file
    cat > terraform.tfvars << EOF
# Terraform variables for ${ENVIRONMENT} environment
# Generated on $(date)

aws_region   = "${AWS_REGION}"
environment  = "${ENVIRONMENT}"
project_name = "${PROJECT_NAME}"
owner_email  = "${OWNER_EMAIL}"

# VPC Configuration
vpc_cidr = "10.0.0.0/16"
private_subnet_cidrs = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
public_subnet_cidrs  = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]

# EKS Configuration
kubernetes_version = "1.28"

node_groups = {
  general = {
    desired_size   = ${ENVIRONMENT == "production" ? 3 : 1}
    min_size      = ${ENVIRONMENT == "production" ? 3 : 1}
    max_size      = ${ENVIRONMENT == "production" ? 10 : 3}
    instance_types = ["${ENVIRONMENT == "production" ? "t3.large" : "t3.medium"}"]
    
    labels = {
      role = "general"
    }
    taints = []
    
    disk_size = 100
  }
}

# RDS Configuration
postgres_version         = "15.5"
db_instance_class       = "${ENVIRONMENT == "production" ? "db.r6g.large" : "db.t3.medium"}"
db_allocated_storage    = ${ENVIRONMENT == "production" ? 100 : 20}
db_max_allocated_storage = ${ENVIRONMENT == "production" ? 1000 : 100}

# ElastiCache Configuration
redis_version   = "7.0"
cache_node_type = "${ENVIRONMENT == "production" ? "cache.r6g.large" : "cache.t3.micro"}"

# Alerting Configuration
alert_email_addresses = [
  "${OWNER_EMAIL}"
]

# Cost Optimization
enable_spot_instances = ${ENVIRONMENT == "production" ? "true" : "false"}

# Security Configuration
enable_waf = ${ENVIRONMENT == "production" ? "true" : "false"}
EOF
    
    success "terraform.tfvars created"
}

# Initialize Terraform
init_terraform() {
    log "Initializing Terraform..."
    
    terraform init \
        -backend-config="bucket=${PROJECT_NAME}-terraform-state" \
        -backend-config="key=infrastructure/terraform.tfstate" \
        -backend-config="region=${AWS_REGION}" \
        -backend-config="dynamodb_table=${PROJECT_NAME}-terraform-locks" \
        -backend-config="encrypt=true"
    
    success "Terraform initialized"
}

# Create workspace
create_workspace() {
    log "Creating Terraform workspace for ${ENVIRONMENT}..."
    
    # Create workspace if it doesn't exist
    if ! terraform workspace select "$ENVIRONMENT" 2>/dev/null; then
        terraform workspace new "$ENVIRONMENT"
    fi
    
    success "Workspace '${ENVIRONMENT}' selected"
}

# Validate configuration
validate_terraform() {
    log "Validating Terraform configuration..."
    
    terraform validate
    
    success "Terraform configuration is valid"
}

# Create plan
create_plan() {
    log "Creating Terraform plan..."
    
    terraform plan -out="${ENVIRONMENT}.tfplan"
    
    success "Terraform plan created: ${ENVIRONMENT}.tfplan"
}

# Main execution
main() {
    log "🚀 Starting Terraform setup for TradeSense ${ENVIRONMENT} infrastructure..."
    
    check_prerequisites
    create_backend_bucket
    create_lock_table
    create_tfvars
    init_terraform
    create_workspace
    validate_terraform
    create_plan
    
    success "✨ Terraform setup complete!"
    log ""
    log "Next steps:"
    log "1. Review the plan: terraform show ${ENVIRONMENT}.tfplan"
    log "2. Apply the plan: terraform apply ${ENVIRONMENT}.tfplan"
    log "3. Or apply directly: terraform apply"
    log ""
    warning "Remember to:"
    warning "- Review and adjust terraform.tfvars as needed"
    warning "- Ensure all required AWS permissions are in place"
    warning "- Back up your state file regularly"
}

# Run main function
main "$@"