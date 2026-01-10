variable "name_prefix" {
  description = "Prefix for resource names"
  type        = string
}

variable "lambda_function_names" {
  description = "List of Lambda function names to monitor"
  type        = list(string)
}

variable "sns_email" {
  description = "Email address for alert notifications"
  type        = string
}