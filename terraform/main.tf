# Main Terraform configuration for TradeSense infrastructure
terraform {
  required_version = ">= 1.5.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.23"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.11"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.5"
    }
  }
  
  # Remote state configuration
  backend "s3" {
    bucket         = "tradesense-terraform-state"
    key            = "infrastructure/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "tradesense-terraform-locks"
  }
}

# Provider configurations
provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Environment = var.environment
      Project     = "TradeSense"
      ManagedBy   = "Terraform"
      Owner       = var.owner_email
    }
  }
}

provider "kubernetes" {
  host                   = module.eks.cluster_endpoint
  cluster_ca_certificate = base64decode(module.eks.cluster_certificate_authority_data)
  
  exec {
    api_version = "client.authentication.k8s.io/v1beta1"
    command     = "aws"
    args = ["eks", "get-token", "--cluster-name", module.eks.cluster_name]
  }
}

provider "helm" {
  kubernetes {
    host                   = module.eks.cluster_endpoint
    cluster_ca_certificate = base64decode(module.eks.cluster_certificate_authority_data)
    
    exec {
      api_version = "client.authentication.k8s.io/v1beta1"
      command     = "aws"
      args = ["eks", "get-token", "--cluster-name", module.eks.cluster_name]
    }
  }
}

# Data sources
data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_caller_identity" "current" {}

# Local variables
locals {
  cluster_name = "${var.project_name}-${var.environment}"
  
  common_tags = {
    Environment = var.environment
    Project     = var.project_name
    ManagedBy   = "Terraform"
  }
}

# VPC Module
module "vpc" {
  source = "./modules/vpc"
  
  name               = local.cluster_name
  cidr              = var.vpc_cidr
  availability_zones = data.aws_availability_zones.available.names
  private_subnets   = var.private_subnet_cidrs
  public_subnets    = var.public_subnet_cidrs
  
  enable_nat_gateway   = true
  single_nat_gateway   = var.environment != "production"
  enable_dns_hostnames = true
  enable_dns_support   = true
  
  # VPC Flow Logs
  enable_flow_log                      = true
  create_flow_log_cloudwatch_iam_role  = true
  create_flow_log_cloudwatch_log_group = true
  
  public_subnet_tags = {
    "kubernetes.io/role/elb"                    = 1
    "kubernetes.io/cluster/${local.cluster_name}" = "shared"
  }
  
  private_subnet_tags = {
    "kubernetes.io/role/internal-elb"           = 1
    "kubernetes.io/cluster/${local.cluster_name}" = "shared"
  }
  
  tags = local.common_tags
}

# EKS Module
module "eks" {
  source = "./modules/eks"
  
  cluster_name    = local.cluster_name
  cluster_version = var.kubernetes_version
  
  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets
  
  # Node groups configuration
  node_groups = var.node_groups
  
  # OIDC provider
  enable_irsa = true
  
  # Cluster addons
  cluster_addons = {
    coredns = {
      resolve_conflicts = "OVERWRITE"
    }
    kube-proxy = {}
    vpc-cni = {
      resolve_conflicts = "OVERWRITE"
    }
    aws-ebs-csi-driver = {
      resolve_conflicts = "OVERWRITE"
    }
  }
  
  # Cluster encryption
  cluster_encryption_policy_name = "${local.cluster_name}-encryption"
  
  tags = local.common_tags
}

# RDS Module
module "rds" {
  source = "./modules/rds"
  
  identifier = "${local.cluster_name}-db"
  
  engine               = "postgres"
  engine_version       = var.postgres_version
  instance_class       = var.db_instance_class
  allocated_storage    = var.db_allocated_storage
  max_allocated_storage = var.db_max_allocated_storage
  
  database_name = var.db_name
  username      = var.db_username
  
  vpc_id                  = module.vpc.vpc_id
  database_subnet_group   = module.vpc.database_subnet_group_name
  allowed_security_groups = [module.eks.cluster_security_group_id]
  
  # Backups
  backup_retention_period = var.environment == "production" ? 30 : 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"
  
  # High availability
  multi_az = var.environment == "production"
  
  # Monitoring
  enabled_cloudwatch_logs_exports = ["postgresql"]
  create_cloudwatch_log_group     = true
  
  # Performance Insights
  performance_insights_enabled = true
  performance_insights_retention_period = 7
  
  tags = local.common_tags
}

# ElastiCache Module
module "elasticache" {
  source = "./modules/elasticache"
  
  name = "${local.cluster_name}-cache"
  
  engine         = "redis"
  engine_version = var.redis_version
  node_type      = var.cache_node_type
  number_cache_nodes = var.environment == "production" ? 3 : 1
  
  vpc_id                  = module.vpc.vpc_id
  subnet_ids              = module.vpc.private_subnets
  allowed_security_groups = [module.eks.cluster_security_group_id]
  
  # Redis specific
  port = 6379
  parameter_group_family = "redis7"
  
  # Automatic failover for production
  automatic_failover_enabled = var.environment == "production"
  
  # Backups
  snapshot_retention_limit = var.environment == "production" ? 7 : 1
  snapshot_window         = "03:00-05:00"
  
  tags = local.common_tags
}

# S3 Buckets
module "s3" {
  source = "./modules/s3"
  
  buckets = {
    uploads = {
      name = "${local.cluster_name}-uploads"
      versioning = true
      lifecycle_rules = [
        {
          id      = "delete-old-versions"
          enabled = true
          noncurrent_version_expiration = {
            days = 90
          }
        }
      ]
    }
    backups = {
      name = "${local.cluster_name}-backups"
      versioning = true
      lifecycle_rules = [
        {
          id      = "transition-to-glacier"
          enabled = true
          transitions = [
            {
              days          = 30
              storage_class = "GLACIER"
            }
          ]
        }
      ]
    }
    static = {
      name = "${local.cluster_name}-static"
      website = {
        index_document = "index.html"
        error_document = "error.html"
      }
    }
  }
  
  tags = local.common_tags
}

# IAM Roles for Service Accounts (IRSA)
module "irsa" {
  source = "./modules/irsa"
  
  cluster_name = module.eks.cluster_name
  oidc_provider_arn = module.eks.oidc_provider_arn
  
  service_accounts = {
    external-secrets = {
      namespace = "external-secrets"
      policy_arns = [aws_iam_policy.external_secrets.arn]
    }
    cluster-autoscaler = {
      namespace = "kube-system"
      policy_arns = [aws_iam_policy.cluster_autoscaler.arn]
    }
    aws-load-balancer-controller = {
      namespace = "kube-system"
      policy_arns = [aws_iam_policy.aws_load_balancer_controller.arn]
    }
    backend = {
      namespace = "tradesense"
      policy_arns = [
        aws_iam_policy.s3_access.arn,
        aws_iam_policy.ses_access.arn
      ]
    }
  }
  
  tags = local.common_tags
}

# CloudFront Distribution
module "cloudfront" {
  source = "./modules/cloudfront"
  
  enabled = var.enable_cdn
  
  aliases = var.environment == "production" ? ["tradesense.com", "www.tradesense.com"] : []
  
  # Origin configuration
  origin_domain_name = module.eks.cluster_endpoint # This would be your ALB domain
  origin_id          = "alb"
  
  # Cache behaviors
  default_cache_behavior = {
    allowed_methods  = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "alb"
    
    forwarded_values = {
      query_string = true
      cookies = {
        forward = "all"
      }
      headers = ["*"]
    }
    
    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 0
    max_ttl                = 0
  }
  
  # Custom error pages
  custom_error_responses = [
    {
      error_code         = 404
      response_code      = 200
      response_page_path = "/index.html"
    }
  ]
  
  # WAF
  web_acl_id = var.environment == "production" ? module.waf.web_acl_id : null
  
  tags = local.common_tags
}

# Monitoring and Alerting
module "monitoring" {
  source = "./modules/monitoring"
  
  cluster_name = local.cluster_name
  
  # CloudWatch Log Groups
  log_groups = {
    "/aws/eks/${local.cluster_name}/cluster" = {
      retention_in_days = 30
    }
    "/aws/rds/instance/${module.rds.db_instance_id}/postgresql" = {
      retention_in_days = 30
    }
  }
  
  # SNS Topics for alerts
  sns_topics = {
    critical_alerts = {
      display_name = "${local.cluster_name} Critical Alerts"
      subscriptions = var.alert_email_addresses
    }
    warning_alerts = {
      display_name = "${local.cluster_name} Warning Alerts"
      subscriptions = var.alert_email_addresses
    }
  }
  
  # CloudWatch Alarms
  alarms = {
    high_cpu_utilization = {
      alarm_name          = "${local.cluster_name}-high-cpu"
      comparison_operator = "GreaterThanThreshold"
      evaluation_periods  = "2"
      metric_name         = "CPUUtilization"
      namespace           = "AWS/EKS"
      period              = "300"
      statistic           = "Average"
      threshold           = "80"
      alarm_description   = "This metric monitors EKS cluster CPU utilization"
      alarm_actions       = [module.monitoring.sns_topic_arns["critical_alerts"]]
    }
    rds_high_connections = {
      alarm_name          = "${local.cluster_name}-rds-connections"
      comparison_operator = "GreaterThanThreshold"
      evaluation_periods  = "1"
      metric_name         = "DatabaseConnections"
      namespace           = "AWS/RDS"
      period              = "300"
      statistic           = "Average"
      threshold           = "80"
      alarm_description   = "RDS connection count is too high"
      alarm_actions       = [module.monitoring.sns_topic_arns["warning_alerts"]]
    }
  }
  
  tags = local.common_tags
}

# Outputs
output "vpc_id" {
  description = "VPC ID"
  value       = module.vpc.vpc_id
}

output "cluster_endpoint" {
  description = "EKS cluster endpoint"
  value       = module.eks.cluster_endpoint
}

output "cluster_name" {
  description = "EKS cluster name"
  value       = module.eks.cluster_name
}

output "database_endpoint" {
  description = "RDS database endpoint"
  value       = module.rds.db_instance_endpoint
  sensitive   = true
}

output "redis_endpoint" {
  description = "ElastiCache Redis endpoint"
  value       = module.elasticache.endpoint
  sensitive   = true
}

output "s3_bucket_names" {
  description = "S3 bucket names"
  value       = module.s3.bucket_names
}