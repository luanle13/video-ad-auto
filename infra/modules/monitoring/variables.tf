variable "name_prefix" {
  description = "Prefix for resource names"
  type        = string
}

variable "aws_region" {
  description = "AWS region for the dashboard"
  type        = string
  default     = "ap-southeast-1"
}

variable "lambda_function_names" {
  description = "List of Lambda function names to monitor"
  type        = list(string)
}

variable "dynamodb_table_names" {
  description = "List of DynamoDB table names to monitor"
  type        = list(string)
  default     = []
}

variable "s3_bucket_names" {
  description = "List of S3 bucket names to monitor"
  type        = list(string)
  default     = []
}

variable "api_gateway_name" {
  description = "Name of the API Gateway to monitor"
  type        = string
  default     = ""
}

variable "step_function_arn" {
  description = "ARN of the Step Functions state machine to monitor"
  type        = string
  default     = ""
}

variable "sns_email" {
  description = "Email address for alert notifications"
  type        = string
}