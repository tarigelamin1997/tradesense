# TradeSense Infrastructure as Code

This directory contains Terraform configurations for deploying the TradeSense infrastructure on AWS.

## 🏗️ Architecture Overview

The infrastructure includes:
- **VPC** with public/private subnets across multiple AZs
- **EKS** cluster with managed node groups
- **RDS PostgreSQL** database with automated backups
- **ElastiCache Redis** for caching
- **S3 buckets** for uploads, backups, and static assets
- **CloudFront CDN** for global content delivery
- **IAM roles** with least privilege access
- **Monitoring** with CloudWatch and alerts

## 📋 Prerequisites

1. **Tools Required**:
   - Terraform >= 1.5.0
   - AWS CLI configured
   - kubectl
   - helm

2. **AWS Permissions**:
   - Administrator access or specific IAM permissions for:
     - EC2, VPC, EKS, RDS, ElastiCache, S3
     - IAM, KMS, CloudWatch, SNS
     - CloudFront, Route53 (if using)

## 🚀 Quick Start

1. **Run the setup script**:
   ```bash
   ./setup-terraform.sh production
   ```

2. **Review and adjust `terraform.tfvars`**:
   ```bash
   vim terraform.tfvars
   ```

3. **Apply the infrastructure**:
   ```bash
   terraform apply
   ```

## 📁 Directory Structure

```
terraform/
├── main.tf                 # Main configuration
├── variables.tf            # Variable definitions
├── terraform.tfvars        # Variable values (git ignored)
├── terraform.tfvars.example # Example values
├── iam-policies.tf         # IAM policies
├── outputs.tf              # Output values
├── modules/                # Reusable modules
│   ├── vpc/                # VPC module
│   ├── eks/                # EKS module
│   ├── rds/                # RDS module
│   ├── elasticache/        # ElastiCache module
│   ├── s3/                 # S3 module
│   ├── cloudfront/         # CloudFront module
│   ├── monitoring/         # Monitoring module
│   └── irsa/               # IAM roles for service accounts
└── setup-terraform.sh      # Setup script
```

## 🔧 Configuration

### Environment-specific Configuration

The infrastructure supports multiple environments:
- `development`
- `staging`
- `production`

Each environment uses:
- Separate Terraform workspace
- Environment-specific variable values
- Isolated resources with environment tags

### Key Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `environment` | Environment name | - |
| `aws_region` | AWS region | us-east-1 |
| `vpc_cidr` | VPC CIDR block | 10.0.0.0/16 |
| `kubernetes_version` | EKS version | 1.28 |
| `node_groups` | EKS node group configuration | See terraform.tfvars.example |

## 🔒 Security

### State Management
- Remote state stored in S3 with encryption
- State locking with DynamoDB
- Versioning enabled on state bucket

### Secrets Management
- Database passwords auto-generated and stored in AWS Secrets Manager
- Encryption at rest for all data stores
- KMS keys for encryption

### Network Security
- Private subnets for compute resources
- Security groups with least privilege
- VPC flow logs enabled
- WAF for production environments

## 🚦 Operations

### Accessing the EKS Cluster

1. **Update kubeconfig**:
   ```bash
   aws eks update-kubeconfig --name $(terraform output -raw cluster_name) --region $(terraform output -raw aws_region)
   ```

2. **Verify access**:
   ```bash
   kubectl get nodes
   ```

### Database Access

1. **Get connection details**:
   ```bash
   terraform output database_endpoint
   ```

2. **Retrieve password from Secrets Manager**:
   ```bash
   aws secretsmanager get-secret-value --secret-id $(terraform output -raw db_secret_name) --query SecretString --output text | jq -r .password
   ```

## 📊 Monitoring

### CloudWatch Dashboards
Access dashboards in AWS Console for:
- EKS cluster metrics
- RDS performance
- Application logs

### Alerts
Alerts are sent to configured email addresses for:
- High CPU/memory utilization
- Database connection issues
- Failed deployments

## 🔄 Maintenance

### Updating Infrastructure

1. **Pull latest changes**:
   ```bash
   git pull origin main
   ```

2. **Plan changes**:
   ```bash
   terraform plan
   ```

3. **Apply changes**:
   ```bash
   terraform apply
   ```

### Backup and Recovery

- **RDS**: Automated daily backups with 30-day retention
- **State file**: Versioned in S3
- **EKS**: Backup using Velero (configure separately)

## 🆘 Troubleshooting

### Common Issues

1. **Terraform init fails**:
   - Check AWS credentials
   - Verify S3 bucket and DynamoDB table exist

2. **EKS node group fails to create**:
   - Check instance type availability in region
   - Verify subnet capacity

3. **RDS creation timeout**:
   - Multi-AZ deployments take longer
   - Check CloudWatch logs

### Getting Help

1. Check Terraform logs:
   ```bash
   TF_LOG=DEBUG terraform apply
   ```

2. AWS Support:
   - CloudFormation stack events
   - CloudTrail logs

## 📚 Additional Resources

- [Terraform AWS Provider Documentation](https://registry.terraform.io/providers/hashicorp/aws/latest)
- [EKS Best Practices](https://aws.github.io/aws-eks-best-practices/)
- [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)

## 🔐 Important Notes

- **Never commit** `terraform.tfvars` or state files
- **Always review** plan output before applying
- **Use workspaces** for environment isolation
- **Regular backups** of state file
- **Rotate credentials** regularly