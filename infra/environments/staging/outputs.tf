output "alb_dns_name" {
  value       = module.alb.alb_dns_name
  description = "Public API endpoint URL"
}

output "vpc_id" {
  value       = module.vpc.vpc_id
  description = "VPC ID"
}

output "rds_endpoint" {
  value       = module.rds_postgres.endpoint
  description = "RDS PostgreSQL Endpoint"
}

output "documents_bucket" {
  value       = module.s3_storage.bucket_id
  description = "S3 Documents Bucket Name"
}
