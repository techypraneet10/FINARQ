variable "aws_region" {
  type        = string
  default     = "us-east-1"
  description = "AWS deployment region"
}

variable "bucket_suffix" {
  type        = string
  description = "Unique suffix for S3 bucket"
}

variable "container_image" {
  type        = string
  description = "ECR Image URI with immutable git tag (strictly never 'latest')"
}

variable "db_password" {
  type        = string
  sensitive   = true
  description = "PostgreSQL master password"
}

variable "redis_auth_token" {
  type        = string
  sensitive   = true
  description = "Redis AUTH token"
}

variable "certificate_arn" {
  type        = string
  description = "ACM TLS Certificate ARN"
}
