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
  description = "Subnet IDs for ElastiCache subnet group"
}

variable "allowed_security_group_ids" {
  type        = list(string)
  default     = []
  description = "Security groups permitted to communicate with Redis"
}

variable "node_type" {
  type        = string
  default     = "cache.m6g.large"
  description = "ElastiCache node type"
}

variable "num_cache_clusters" {
  type        = number
  default     = 2
  description = "Number of cache nodes (1 primary + replicas)"
}

variable "multi_az" {
  type        = bool
  default     = true
  description = "Enable Multi-AZ automatic failover"
}

variable "auth_token" {
  type        = string
  sensitive   = true
  description = "Redis AUTH password / token"
}

variable "snapshot_retention_days" {
  type        = number
  default     = 7
  description = "Automated daily backup retention days"
}

variable "tags" {
  type        = map(string)
  default     = {}
  description = "Resource tags"
}
