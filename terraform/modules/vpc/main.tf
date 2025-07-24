# VPC Module for TradeSense
locals {
  max_subnet_length = max(
    length(var.private_subnets),
    length(var.public_subnets)
  )
  nat_gateway_count = var.single_nat_gateway ? 1 : var.one_nat_gateway_per_az ? length(var.azs) : local.max_subnet_length

  # Ensure we have enough AZs
  azs = length(var.availability_zones) > 0 ? var.availability_zones : data.aws_availability_zones.available.names
}

data "aws_availability_zones" "available" {
  state = "available"
}

# VPC
resource "aws_vpc" "this" {
  cidr_block           = var.cidr
  enable_dns_hostnames = var.enable_dns_hostnames
  enable_dns_support   = var.enable_dns_support

  tags = merge(
    var.tags,
    {
      Name = var.name
    }
  )
}

# Internet Gateway
resource "aws_internet_gateway" "this" {
  count = var.create_igw && length(var.public_subnets) > 0 ? 1 : 0

  vpc_id = aws_vpc.this.id

  tags = merge(
    var.tags,
    {
      Name = var.name
    }
  )
}

# Public Subnets
resource "aws_subnet" "public" {
  count = length(var.public_subnets)

  vpc_id                  = aws_vpc.this.id
  cidr_block              = element(var.public_subnets, count.index)
  availability_zone       = element(local.azs, count.index)
  map_public_ip_on_launch = true

  tags = merge(
    var.tags,
    var.public_subnet_tags,
    {
      Name = format(
        "%s-public-%s",
        var.name,
        element(local.azs, count.index),
      )
      Type = "public"
    }
  )
}

# Private Subnets
resource "aws_subnet" "private" {
  count = length(var.private_subnets)

  vpc_id            = aws_vpc.this.id
  cidr_block        = element(var.private_subnets, count.index)
  availability_zone = element(local.azs, count.index)

  tags = merge(
    var.tags,
    var.private_subnet_tags,
    {
      Name = format(
        "%s-private-%s",
        var.name,
        element(local.azs, count.index),
      )
      Type = "private"
    }
  )
}

# Database Subnets
resource "aws_subnet" "database" {
  count = length(var.database_subnets)

  vpc_id            = aws_vpc.this.id
  cidr_block        = element(var.database_subnets, count.index)
  availability_zone = element(local.azs, count.index)

  tags = merge(
    var.tags,
    var.database_subnet_tags,
    {
      Name = format(
        "%s-database-%s",
        var.name,
        element(local.azs, count.index),
      )
      Type = "database"
    }
  )
}

# Elastic IPs for NAT Gateways
resource "aws_eip" "nat" {
  count = var.enable_nat_gateway ? local.nat_gateway_count : 0

  domain = "vpc"

  tags = merge(
    var.tags,
    {
      Name = format(
        "%s-nat-%s",
        var.name,
        element(local.azs, count.index),
      )
    }
  )

  depends_on = [aws_internet_gateway.this]
}

# NAT Gateways
resource "aws_nat_gateway" "this" {
  count = var.enable_nat_gateway ? local.nat_gateway_count : 0

  allocation_id = element(aws_eip.nat[*].id, count.index)
  subnet_id     = element(aws_subnet.public[*].id, count.index)

  tags = merge(
    var.tags,
    {
      Name = format(
        "%s-nat-%s",
        var.name,
        element(local.azs, count.index),
      )
    }
  )

  depends_on = [aws_internet_gateway.this]
}

# Public Route Table
resource "aws_route_table" "public" {
  count = length(var.public_subnets) > 0 ? 1 : 0

  vpc_id = aws_vpc.this.id

  tags = merge(
    var.tags,
    {
      Name = "${var.name}-public"
      Type = "public"
    }
  )
}

# Public Routes
resource "aws_route" "public_internet_gateway" {
  count = var.create_igw && length(var.public_subnets) > 0 ? 1 : 0

  route_table_id         = aws_route_table.public[0].id
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = aws_internet_gateway.this[0].id

  timeouts {
    create = "5m"
  }
}

# Private Route Tables
resource "aws_route_table" "private" {
  count = local.nat_gateway_count

  vpc_id = aws_vpc.this.id

  tags = merge(
    var.tags,
    {
      Name = format(
        "%s-private-%s",
        var.name,
        element(local.azs, count.index),
      )
      Type = "private"
    }
  )
}

# Private Routes
resource "aws_route" "private_nat_gateway" {
  count = var.enable_nat_gateway ? local.nat_gateway_count : 0

  route_table_id         = element(aws_route_table.private[*].id, count.index)
  destination_cidr_block = "0.0.0.0/0"
  nat_gateway_id         = element(aws_nat_gateway.this[*].id, count.index)

  timeouts {
    create = "5m"
  }
}

# Route Table Associations - Public
resource "aws_route_table_association" "public" {
  count = length(var.public_subnets)

  subnet_id      = element(aws_subnet.public[*].id, count.index)
  route_table_id = aws_route_table.public[0].id
}

# Route Table Associations - Private
resource "aws_route_table_association" "private" {
  count = length(var.private_subnets)

  subnet_id = element(aws_subnet.private[*].id, count.index)
  route_table_id = element(
    aws_route_table.private[*].id,
    var.single_nat_gateway ? 0 : count.index,
  )
}

# Database Subnet Group
resource "aws_db_subnet_group" "database" {
  count = length(var.database_subnets) > 0 ? 1 : 0

  name       = var.name
  subnet_ids = aws_subnet.database[*].id

  tags = merge(
    var.tags,
    {
      Name = var.name
    }
  )
}

# VPC Flow Logs
resource "aws_flow_log" "this" {
  count = var.enable_flow_log ? 1 : 0

  iam_role_arn    = var.create_flow_log_cloudwatch_iam_role ? aws_iam_role.vpc_flow_log[0].arn : var.flow_log_cloudwatch_iam_role_arn
  log_destination = var.create_flow_log_cloudwatch_log_group ? aws_cloudwatch_log_group.flow_log[0].arn : var.flow_log_cloudwatch_log_group_arn
  traffic_type    = var.flow_log_traffic_type
  vpc_id          = aws_vpc.this.id

  tags = merge(
    var.tags,
    {
      Name = var.name
    }
  )
}

# CloudWatch Log Group for VPC Flow Logs
resource "aws_cloudwatch_log_group" "flow_log" {
  count = var.create_flow_log_cloudwatch_log_group && var.enable_flow_log ? 1 : 0

  name              = "/aws/vpc/flowlogs/${var.name}"
  retention_in_days = var.flow_log_retention_in_days
  kms_key_id        = var.flow_log_kms_key_id

  tags = merge(
    var.tags,
    {
      Name = var.name
    }
  )
}

# IAM Role for VPC Flow Logs
resource "aws_iam_role" "vpc_flow_log" {
  count = var.create_flow_log_cloudwatch_iam_role && var.enable_flow_log ? 1 : 0

  name               = "${var.name}-vpc-flow-log-role"
  assume_role_policy = data.aws_iam_policy_document.flow_log_assume_role[0].json

  tags = merge(
    var.tags,
    {
      Name = "${var.name}-vpc-flow-log-role"
    }
  )
}

data "aws_iam_policy_document" "flow_log_assume_role" {
  count = var.create_flow_log_cloudwatch_iam_role && var.enable_flow_log ? 1 : 0

  statement {
    principals {
      type        = "Service"
      identifiers = ["vpc-flow-logs.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role_policy" "vpc_flow_log_cloudwatch" {
  count = var.create_flow_log_cloudwatch_iam_role && var.enable_flow_log ? 1 : 0

  name   = "${var.name}-vpc-flow-log-policy"
  role   = aws_iam_role.vpc_flow_log[0].id
  policy = data.aws_iam_policy_document.flow_log_cloudwatch[0].json
}

data "aws_iam_policy_document" "flow_log_cloudwatch" {
  count = var.create_flow_log_cloudwatch_iam_role && var.enable_flow_log ? 1 : 0

  statement {
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents",
      "logs:DescribeLogGroups",
      "logs:DescribeLogStreams",
    ]

    resources = ["*"]
  }
}