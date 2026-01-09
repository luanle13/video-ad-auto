variable "name_prefix" {
  description = "Prefix for resource names"
  type        = string
}

variable "environment" {
  description = "Environment name (dev/prod)"
  type        = string
}

variable "callback_urls" {
  description = "Callback URLs for authentication"
  type        = list(string)
}

variable "logout_urls" {
  description = "Logout URLs for authentication"
  type        = list(string)
  default     = []
}