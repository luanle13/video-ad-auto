variable "project_name" {
  description = "Project name for resource naming"
  type        = string
}

variable "environment" {
  description = "Environment (dev/prod)"
  type        = string
}

variable "agent_lambda_arn" {
  description = "ARN of the agent worker Lambda function"
  type        = string
}

variable "tts_lambda_arn" {
  description = "ARN of the TTS worker Lambda function"
  type        = string
}

variable "video_lambda_arn" {
  description = "ARN of the video worker Lambda function"
  type        = string
}

variable "dynamodb_jobs_table_name" {
  description = "Name of the DynamoDB jobs table"
  type        = string
}

variable "dynamodb_jobs_table_arn" {
  description = "ARN of the DynamoDB jobs table"
  type        = string
}

variable "s3_videos_bucket_arn" {
  description = "ARN of the S3 videos bucket"
  type        = string
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}
