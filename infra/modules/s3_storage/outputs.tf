output "bucket_id" {
  value       = aws_s3_bucket.documents.id
  description = "Name/ID of the documents S3 bucket"
}

output "bucket_arn" {
  value       = aws_s3_bucket.documents.arn
  description = "ARN of the documents S3 bucket"
}

output "bucket_domain_name" {
  value       = aws_s3_bucket.documents.bucket_domain_name
  description = "Domain name of the documents S3 bucket"
}
