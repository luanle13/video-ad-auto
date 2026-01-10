variable "name_prefix" {
  description = "Prefix for resource names"
  type        = string
}

variable "agent_lambda_arn" {
  description = "ARN of the agent Lambda function"
  type        = string
}

variable "tts_lambda_arn" {
  description = "ARN of the TTS Lambda function"
  type        = string
}

variable "video_lambda_arn" {
  description = "ARN of the video generation Lambda function"
  type        = string
}