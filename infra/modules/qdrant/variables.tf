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
  description = "Subnet IDs for deploying Qdrant compute tasks"
}

variable "allowed_security_group_ids" {
  type        = list(string)
  default     = []
  description = "Security groups allowed to query Qdrant (API, Worker)"
}

variable "ecs_cluster_id" {
  type        = string
  description = "ECS cluster ID where Qdrant runs"
}

variable "service_discovery_namespace_id" {
  type        = string
  description = "Private DNS Service Discovery namespace ID for service-to-service communication"
}

variable "aws_region" {
  type        = string
  default     = "us-east-1"
  description = "AWS deployment region"
}

variable "execution_role_arn" {
  type        = string
  description = "ECS Task execution role ARN"
}

variable "task_role_arn" {
  type        = string
  description = "ECS Task role ARN"
}

variable "qdrant_image" {
  type        = string
  default     = "qdrant/qdrant:v1.9.0"
  description = "Qdrant Docker container image tag"
}

variable "cpu" {
  type        = number
  default     = 1024
  description = "Fargate vCPU allocation (1024 = 1 vCPU)"
}

variable "memory" {
  type        = number
  default     = 2048
  description = "Fargate memory allocation in MB (2048 = 2GB)"
}

variable "tags" {
  type        = map(string)
  default     = {}
  description = "Resource tags"
}
