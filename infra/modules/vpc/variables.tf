variable "environment" {
  type        = string
  description = "Target deployment environment (dev, staging, production)"
}

variable "vpc_cidr" {
  type        = string
  default     = "10.0.0.0/16"
  description = "CIDR block for the VPC"
}

variable "availability_zones" {
  type        = list(string)
  description = "List of availability zones to spread subnets across"
}

variable "public_subnet_cidrs" {
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
  description = "CIDR blocks for public subnets"
}

variable "private_app_subnet_cidrs" {
  type        = list(string)
  default     = ["10.0.10.0/24", "10.0.20.0/24"]
  description = "CIDR blocks for private application compute subnets"
}

variable "private_data_subnet_cidrs" {
  type        = list(string)
  default     = ["10.0.100.0/24", "10.0.200.0/24"]
  description = "CIDR blocks for private database and data store subnets"
}

variable "single_nat_gateway" {
  type        = bool
  default     = false
  description = "Whether to use a single NAT Gateway (for cost-efficiency in dev) or Multi-AZ NAT Gateways"
}

variable "tags" {
  type        = map(string)
  default     = {}
  description = "Tags applied to all network resources"
}
