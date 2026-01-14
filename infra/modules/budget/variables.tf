variable "name_prefix" {
  description = "Prefix for resource names"
  type        = string
}

variable "environment" {
  description = "Environment name (dev/prod)"
  type        = string
}

variable "budget_limit" {
  description = "Monthly budget limit in USD"
  type        = string
  default     = "300"
}

variable "lambda_budget_limit" {
  description = "Monthly Lambda budget limit in USD"
  type        = string
  default     = "60"
}

variable "notification_email" {
  description = "Email address for budget notifications"
  type        = string
}
