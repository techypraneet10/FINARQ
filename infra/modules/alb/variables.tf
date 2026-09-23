variable "environment" {
  type        = string
  description = "Target deployment environment (dev, staging, production)"
}

variable "vpc_id" {
  type        = string
  description = "Target VPC ID"
}

variable "public_subnet_ids" {
  type        = list(string)
  description = "List of public subnet IDs to attach ALB to"
}

variable "certificate_arn" {
  type        = string
  default     = null
  description = "ACM TLS Certificate ARN for HTTPS listener"
}

variable "deletion_protection" {
  type        = bool
  default     = true
  description = "Enable ALB deletion protection in production"
}

variable "tags" {
  type        = map(string)
  default     = {}
  description = "Resource tags"
}
