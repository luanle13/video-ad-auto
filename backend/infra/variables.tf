variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "ai-video"
}

variable "environment" {
  description = "Deployment environment"
  type        = string
  default     = "dev"

  validation {
    condition = contains([
      "dev",
      "prod",
    ], var.environment)
    error_message = "Environment must be either 'dev' or 'prod'."
  }
}

variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "ap-southeast-1"
}

variable "cognito_callback_urls" {
  description = "Callback URLs for Cognito authentication"
  type        = list(string)
  default     = []
}

variable "lambda_memory_size" {
  description = "Memory size for Lambda functions in MB"
  type        = number
  default     = 512
}

variable "lambda_timeout" {
  description = "Timeout for standard Lambda functions in seconds"
  type        = number
  default     = 30
}

variable "agent_lambda_timeout" {
  description = "Timeout for agent Lambda functions in seconds"
  type        = number
  default     = 180
}

variable "video_lambda_timeout" {
  description = "Timeout for video generation Lambda functions in seconds"
  type        = number
  default     = 600
}

variable "budget_limit" {
  description = "Monthly budget limit in USD"
  type        = number
  default     = 100
}

variable "budget_notification_email" {
  description = "Email address for budget notifications"
  type        = string
}