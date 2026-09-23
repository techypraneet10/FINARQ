variable "environment" {
  type        = string
  description = "Target deployment environment (dev, staging, production)"
}

variable "bucket_suffix" {
  type        = string
  description = "Unique account/region suffix to guarantee global S3 bucket uniqueness"
}

variable "force_destroy" {
  type        = bool
  default     = false
  description = "Allow destroying non-empty bucket (false for prod, true only for ephemeral dev/test)"
}

variable "kms_key_arn" {
  type        = string
  default     = null
  description = "ARN of customer KMS key for S3 bucket encryption (null defaults to AES256)"
}

variable "tags" {
  type        = map(string)
  default     = {}
  description = "Tags applied to S3 resources"
}
