variable "environment" {
  type        = string
  description = "Target deployment environment (dev, staging, production)"
}

variable "vpc_id" {
  type        = string
  description = "ID of the target VPC"
}

variable "subnet_ids" {
  type        = list(string)
  description = "List of isolated private data subnet IDs for DB subnet group"
}

variable "allowed_security_group_ids" {
  type        = list(string)
  default     = []
  description = "List of compute security group IDs permitted to connect to PostgreSQL"
}

variable "database_name" {
  type        = string
  default     = "financial_rag_db"
  description = "Name of the default relational database"
}

variable "master_username" {
  type        = string
  default     = "dbadmin"
  description = "Master DB username"
}

variable "master_password" {
  type        = string
  sensitive   = true
  description = "Master DB password (managed via AWS Secrets Manager or secure variable)"
}

variable "instance_class" {
  type        = string
  default     = "db.r6g.large"
  description = "RDS instance class"
}

variable "allocated_storage_gb" {
  type        = number
  default     = 50
  description = "Initial allocated storage in GB"
}

variable "max_allocated_storage_gb" {
  type        = number
  default     = 500
  description = "Maximum storage limit for storage autoscaling in GB"
}

variable "storage_type" {
  type        = string
  default     = "gp3"
  description = "Storage type (gp3, io1, io2)"
}

variable "multi_az" {
  type        = bool
  default     = true
  description = "Enable Multi-AZ high availability deployment"
}

variable "backup_retention_days" {
  type        = number
  default     = 30
  description = "Automated backup retention window in days"
}

variable "deletion_protection" {
  type        = bool
  default     = true
  description = "Protect database from accidental deletion"
}

variable "skip_final_snapshot" {
  type        = bool
  default     = false
  description = "Whether to skip final DB snapshot before destruction"
}

variable "kms_key_arn" {
  type        = string
  default     = null
  description = "ARN of customer-managed KMS key for EBS storage encryption"
}

variable "performance_insights_enabled" {
  type        = bool
  default     = true
  description = "Enable RDS Performance Insights"
}

variable "tags" {
  type        = map(string)
  default     = {}
  description = "Tags applied to all RDS resources"
}
