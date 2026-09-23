# ==============================================================================
# Redis ElastiCache Module - High-Availability In-Memory Caching
# ==============================================================================

resource "aws_elasticache_subnet_group" "main" {
  name        = "${var.environment}-financial-rag-redis-subnet-group"
  subnet_ids  = var.subnet_ids
  description = "Subnet group for Financial RAG Redis cluster"

  tags = merge(
    var.tags,
    {
      Environment = var.environment
    }
  )
}

resource "aws_security_group" "redis" {
  name        = "${var.environment}-financial-rag-redis-sg"
  description = "Controls access to Redis from API and Worker tasks"
  vpc_id      = var.vpc_id

  ingress {
    description     = "Inbound Redis port 6379 from API and Worker compute"
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = var.allowed_security_group_ids
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(
    var.tags,
    {
      Name        = "${var.environment}-redis-sg"
      Environment = var.environment
    }
  )
}

resource "aws_elasticache_parameter_group" "redis7" {
  name   = "${var.environment}-financial-rag-redis7-params"
  family = "redis7"

  parameter {
    name  = "maxmemory-policy"
    value = "volatile-lru"
  }

  tags = merge(
    var.tags,
    {
      Environment = var.environment
    }
  )
}

resource "aws_elasticache_replication_group" "main" {
  replication_group_id       = "${var.environment}-financial-rag-redis"
  description                = "Redis cluster for Financial RAG caching and queues"
  node_type                  = var.node_type
  port                       = 6379
  parameter_group_name       = aws_elasticache_parameter_group.redis7.name
  subnet_group_name          = aws_elasticache_subnet_group.main.name
  security_group_ids         = [aws_security_group.redis.id]

  automatic_failover_enabled = var.multi_az
  multi_az_enabled           = var.multi_az
  num_cache_clusters         = var.num_cache_clusters

  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  auth_token                 = var.auth_token

  auto_minor_version_upgrade = true
  maintenance_window         = "sun:03:00-sun:04:00"
  snapshot_retention_limit   = var.snapshot_retention_days
  snapshot_window            = "01:00-02:00"

  tags = merge(
    var.tags,
    {
      Name        = "${var.environment}-redis-cluster"
      Environment = var.environment
    }
  )
}
