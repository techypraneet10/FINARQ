# ==============================================================================
# Staging Environment (staging) - Production Parity Verification
# ==============================================================================

terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
  default_tags {
    tags = {
      Environment = "staging"
      Project     = "financial-rag-platform"
      ManagedBy   = "terraform"
    }
  }
}

module "vpc" {
  source             = "../../modules/vpc"
  environment        = "staging"
  vpc_cidr           = "10.20.0.0/16"
  availability_zones = ["${var.aws_region}a", "${var.aws_region}b"]
  single_nat_gateway = false
}

module "s3_storage" {
  source        = "../../modules/s3_storage"
  environment   = "staging"
  bucket_suffix = var.bucket_suffix
  force_destroy = false
}

module "rds_postgres" {
  source                     = "../../modules/rds_postgres"
  environment                = "staging"
  vpc_id                     = module.vpc.vpc_id
  subnet_ids                 = module.vpc.private_data_subnet_ids
  allowed_security_group_ids = [module.compute.api_security_group_id, module.compute.worker_security_group_id]
  instance_class             = "db.r6g.large"
  allocated_storage_gb       = 50
  max_allocated_storage_gb   = 200
  multi_az                   = true
  backup_retention_days      = 14
  deletion_protection        = true
  skip_final_snapshot        = false
  master_password            = var.db_password
}

module "alb" {
  source              = "../../modules/alb"
  environment         = "staging"
  vpc_id              = module.vpc.vpc_id
  public_subnet_ids   = module.vpc.public_subnet_ids
  certificate_arn     = var.certificate_arn
  deletion_protection = true
}

resource "aws_ecs_cluster" "main" {
  name = "staging-financial-rag-cluster"
}

resource "aws_service_discovery_private_dns_namespace" "main" {
  name = "financial-rag.local"
  vpc  = module.vpc.vpc_id
}

module "qdrant" {
  source                         = "../../modules/qdrant"
  environment                    = "staging"
  vpc_id                         = module.vpc.vpc_id
  subnet_ids                     = module.vpc.private_app_subnet_ids
  allowed_security_group_ids     = [module.compute.api_security_group_id, module.compute.worker_security_group_id]
  ecs_cluster_id                 = aws_ecs_cluster.main.id
  service_discovery_namespace_id = aws_service_discovery_private_dns_namespace.main.id
  execution_role_arn             = module.compute.task_execution_role_arn
  task_role_arn                  = module.compute.app_task_role_arn
  cpu                            = 1024
  memory                         = 2048
}

module "redis" {
  source                     = "../../modules/redis"
  environment                = "staging"
  vpc_id                     = module.vpc.vpc_id
  subnet_ids                 = module.vpc.private_data_subnet_ids
  allowed_security_group_ids = [module.compute.api_security_group_id, module.compute.worker_security_group_id]
  node_type                  = "cache.m6g.large"
  num_cache_clusters         = 2
  multi_az                   = true
  auth_token                 = var.redis_auth_token
}

module "compute" {
  source                = "../../modules/compute_api_worker"
  environment           = "staging"
  vpc_id                = module.vpc.vpc_id
  subnet_ids            = module.vpc.private_app_subnet_ids
  ecs_cluster_id        = aws_ecs_cluster.main.id
  alb_security_group_id = module.alb.security_group_id
  target_group_arn      = module.alb.target_group_arn
  documents_bucket_arn  = module.s3_storage.bucket_arn
  container_image       = var.container_image
  api_desired_count     = 2
  worker_desired_count  = 2
  api_cpu               = 1024
  api_memory            = 2048
  worker_cpu            = 2048
  worker_memory         = 4096
  worker_concurrency    = 4

  common_environment_variables = [
    { name = "APP_ENVIRONMENT", value = "staging" },
    { name = "LOG_LEVEL", value = "INFO" },
    { name = "LOG_FORMAT", value = "json" },
    { name = "DB_HOST", value = module.rds_postgres.address },
    { name = "DB_PORT", value = "5432" },
    { name = "DB_NAME", value = module.rds_postgres.database_name },
    { name = "DB_USER", value = "dbadmin" },
    { name = "STORAGE_ADAPTER", value = "s3" },
    { name = "STORAGE_BUCKET_DOCUMENTS", value = module.s3_storage.bucket_id },
    { name = "QDRANT_HOST", value = "qdrant.financial-rag.local" },
    { name = "QDRANT_PORT", value = "6333" },
    { name = "REDIS_HOST", value = module.redis.primary_endpoint_address },
    { name = "REDIS_PORT", value = "6379" }
  ]
}
