variable "name_prefix" {
  description = "Prefix for resource names"
  type        = string
}

variable "budget_limit" {
  description = "Monthly budget limit in USD"
  type        = number
}

variable "notification_email" {
  description = "Email address for budget notifications"
  type        = string
}