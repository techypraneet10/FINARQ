variable "environment" {
  type        = string
  description = "Target deployment environment (dev, staging, production)"
}

variable "vpc_id" {
  type        = string
  description = "Target VPC ID"
}

variable "subnet_ids" {
  type        = list(string)
  description = "Private app subnet IDs for compute tasks"
}

variable "ecs_cluster_id" {
  type        = string
  description = "ECS cluster ID"
}

variable "alb_security_group_id" {
  type        = string
  description = "Security Group ID of the Application Load Balancer"
}

variable "target_group_arn" {
  type        = string
  description = "ALB target group ARN for routing HTTP API traffic"
}

variable "documents_bucket_arn" {
  type        = string
  description = "ARN of documents S3 bucket for task IAM permissions"
}

variable "container_image" {
  type        = string
  description = "Immutable ECR container image URI with Git SHA (never 'latest')"
}

variable "aws_region" {
  type        = string
  default     = "us-east-1"
  description = "AWS region"
}

variable "api_desired_count" {
  type        = number
  default     = 2
  description = "Desired number of API task replicas"
}

variable "worker_desired_count" {
  type        = number
  default     = 2
  description = "Desired number of Worker task replicas"
}

variable "api_cpu" {
  type        = number
  default     = 1024
  description = "CPU units for API tasks (1024 = 1 vCPU)"
}

variable "api_memory" {
  type        = number
  default     = 2048
  description = "Memory in MB for API tasks"
}

variable "worker_cpu" {
  type        = number
  default     = 2048
  description = "CPU units for Worker tasks"
}

variable "worker_memory" {
  type        = number
  default     = 4096
  description = "Memory in MB for Worker tasks"
}

variable "worker_concurrency" {
  type        = number
  default     = 4
  description = "Worker asynchronous job concurrency limit"
}

variable "common_environment_variables" {
  type        = list(object({ name = string, value = string }))
  default     = []
  description = "Common environment variables passed to containers"
}

variable "common_secrets" {
  type        = list(object({ name = string, valueFrom = string }))
  default     = []
  description = "Secrets fetched from AWS Secrets Manager / SSM Parameter Store"
}

variable "tags" {
  type        = map(string)
  default     = {}
  description = "Resource tags"
}
