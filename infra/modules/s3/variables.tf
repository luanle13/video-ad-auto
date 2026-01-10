variable "name_prefix" {
  description = "Prefix for resource names"
  type        = string
}

variable "name_suffix" {
  description = "Suffix for resource names"
  type        = string
}

variable "environment" {
  description = "Environment name (dev/prod)"
  type        = string
}

variable "lifecycle_expiration_days" {
  description = "Number of days after which objects expire in lifecycle rules"
  type        = number
  default     = 30
}