output "api_endpoint" {
  description = "API Gateway endpoint URL"
  value       = "https://${aws_api_gateway_rest_api.video_api.id}.execute-api.${var.aws_region}.amazonaws.com/${var.environment}"
}

output "cognito_user_pool_id" {
  description = "Cognito User Pool ID"
  value       = aws_cognito_user_pool.main.id
}

output "cognito_app_client_id" {
  description = "Cognito App Client ID"
  value       = aws_cognito_user_pool_client.main.id
}

output "s3_images_bucket" {
  description = "S3 bucket for storing product images"
  value       = aws_s3_bucket.images.id
}

output "s3_videos_bucket" {
  description = "S3 bucket for storing generated videos"
  value       = aws_s3_bucket.videos.id
}

output "cloudfront_distribution_domain" {
  description = "CloudFront distribution domain name"
  value       = aws_cloudfront_distribution.video_distribution.domain_name
}

output "state_machine_arn" {
  description = "ARN of the Step Functions state machine"
  value       = aws_sfn_state_machine.video_generation.id
}