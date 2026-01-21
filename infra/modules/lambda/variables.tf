variable "function_name" {
  description = "Name of the Lambda function"
  type        = string
}

variable "handler" {
  description = "Function within your code that is called to start execution"
  type        = string
  default     = null
}

variable "image_command" {
  description = "CMD override for container-based Lambda (handler path)"
  type        = list(string)
  default     = null
}

variable "runtime" {
  description = "Lambda runtime environment"
  type        = string
  default     = "python3.11"
}

variable "timeout" {
  description = "Function timeout in seconds"
  type        = number
}

variable "memory_size" {
  description = "Amount of memory in MB allocated to the function"
  type        = number
}

variable "environment_variables" {
  description = "Map of environment variables to set in the function"
  type        = map(string)
  default     = {}
}

variable "s3_bucket" {
  description = "S3 bucket containing the deployment package"
  type        = string
  default     = null
}

variable "s3_key" {
  description = "S3 key for the deployment package"
  type        = string
  default     = null
}

variable "image_uri" {
  description = "ECR image URI for container-based Lambda"
  type        = string
  default     = null
}

variable "package_type" {
  description = "Lambda package type: Zip or Image"
  type        = string
  default     = "Zip"
}

variable "layers" {
  description = "List of Lambda layer ARNs to attach to the function"
  type        = list(string)
  default     = []
}

variable "vpc_config" {
  description = "VPC configuration for the Lambda function"
  type        = object({
    subnet_ids         = list(string)
    security_group_ids = list(string)
  })
  default = null
}