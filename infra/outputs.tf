output "api_endpoint" {
  description = "API Gateway endpoint URL"
  value       = module.api_gateway.api_endpoint
}

output "cognito_user_pool_id" {
  description = "Cognito User Pool ID"
  value       = module.cognito.user_pool_id
}

output "cognito_app_client_id" {
  description = "Cognito App Client ID"
  value       = module.cognito.app_client_id
}

output "s3_images_bucket" {
  description = "S3 bucket for storing product images"
  value       = module.s3.images_bucket_name
}

output "s3_videos_bucket" {
  description = "S3 bucket for storing generated videos"
  value       = module.s3.videos_bucket_name
}

output "s3_webapp_bucket" {
  description = "S3 bucket for webapp static files"
  value       = module.s3.webapp_bucket_name
}

output "deployment_bucket" {
  description = "S3 bucket for Lambda deployment packages"
  value       = aws_s3_bucket.deployment.id
}

output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID"
  value       = module.cloudfront.distribution_id
}

output "cloudfront_domain_name" {
  description = "CloudFront distribution domain name"
  value       = module.cloudfront.distribution_domain
}

output "state_machine_arn" {
  description = "ARN of the Step Functions state machine"
  value       = module.stepfunctions.state_machine_arn
}

output "lambda_api_arn" {
  description = "ARN of the API Lambda function"
  value       = module.lambda_api.function_arn
}

output "lambda_agents_arn" {
  description = "ARN of the Agents Lambda function"
  value       = module.lambda_agents.function_arn
}

output "lambda_tts_arn" {
  description = "ARN of the TTS Lambda function"
  value       = module.lambda_tts.function_arn
}

output "lambda_video_arn" {
  description = "ARN of the Video Lambda function"
  value       = module.lambda_video.function_arn
}
