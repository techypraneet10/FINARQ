output "alb_dns_name" {
  value       = module.alb.alb_dns_name
  description = "Public production API endpoint URL"
}

output "vpc_id" {
  value       = module.vpc.vpc_id
  description = "Production VPC ID"
}

output "rds_endpoint" {
  value       = module.rds_postgres.endpoint
  description = "Production RDS PostgreSQL Endpoint"
}

output "documents_bucket" {
  value       = module.s3_storage.bucket_id
  description = "Production S3 Documents Bucket Name"
}

output "kms_key_arn" {
  value       = aws_kms_key.main.arn
  description = "Production KMS Key ARN"
}
