# ==============================================================================
# RDS PostgreSQL Module - Multi-AZ Relational Persistence
# ==============================================================================

resource "aws_db_subnet_group" "main" {
  name        = "${var.environment}-financial-rag-db-subnet-group"
  subnet_ids  = var.subnet_ids
  description = "Subnet group for Financial RAG PostgreSQL RDS"

  tags = merge(
    var.tags,
    {
      Name        = "${var.environment}-db-subnet-group"
      Environment = var.environment
    }
  )
}

resource "aws_security_group" "rds" {
  name        = "${var.environment}-financial-rag-rds-sg"
  description = "Controls inbound access to PostgreSQL RDS from private app subnet"
  vpc_id      = var.vpc_id

  ingress {
    description     = "Allow inbound PostgreSQL connections from API and Worker compute"
    from_port       = 5432
    to_port         = 5432
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
      Name        = "${var.environment}-rds-sg"
      Environment = var.environment
    }
  )
}

resource "aws_db_parameter_group" "postgres16" {
  name   = "${var.environment}-financial-rag-pg16-params"
  family = "postgres16"

  parameter {
    name  = "rds.force_ssl"
    value = "1"
  }

  parameter {
    name  = "statement_timeout"
    value = "30000" # 30s max query execution
  }

  parameter {
    name  = "log_connections"
    value = "1"
  }

  parameter {
    name  = "log_disconnections"
    value = "1"
  }

  tags = merge(
    var.tags,
    {
      Environment = var.environment
    }
  )
}

resource "aws_db_instance" "main" {
  identifier     = "${var.environment}-financial-rag-postgres"
  engine         = "postgres"
  engine_version = "16.2"
  instance_class = var.instance_class

  allocated_storage     = var.allocated_storage_gb
  max_allocated_storage = var.max_allocated_storage_gb
  storage_type          = var.storage_type
  storage_encrypted     = true
  kms_key_id            = var.kms_key_arn

  db_name  = var.database_name
  username = var.master_username
  password = var.master_password
  port     = 5432

  multi_az               = var.multi_az
  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  parameter_group_name   = aws_db_parameter_group.postgres16.name

  backup_retention_period   = var.backup_retention_days
  backup_window             = "03:00-04:00"
  maintenance_window        = "sun:04:30-sun:05:30"
  auto_minor_version_upgrade = true
  deletion_protection       = var.deletion_protection
  skip_final_snapshot       = var.skip_final_snapshot
  final_snapshot_identifier = "${var.environment}-financial-rag-postgres-final-snapshot"

  performance_insights_enabled    = var.performance_insights_enabled
  performance_insights_retention_period = var.performance_insights_enabled ? 7 : null

  tags = merge(
    var.tags,
    {
      Name        = "${var.environment}-postgres-instance"
      Environment = var.environment
    }
  )
}
