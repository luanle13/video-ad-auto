output "images_bucket_name" {
  description = "Name of the images bucket"
  value       = aws_s3_bucket.images.id
}

output "images_bucket_arn" {
  description = "ARN of the images bucket"
  value       = aws_s3_bucket.images.arn
}

output "videos_bucket_name" {
  description = "Name of the videos bucket"
  value       = aws_s3_bucket.videos.id
}

output "videos_bucket_arn" {
  description = "ARN of the videos bucket"
  value       = aws_s3_bucket.videos.arn
}

output "webapp_bucket_name" {
  description = "Name of the webapp bucket"
  value       = aws_s3_bucket.webapp.id
}

output "webapp_bucket_arn" {
  description = "ARN of the webapp bucket"
  value       = aws_s3_bucket.webapp.arn
}

output "bucket_arns" {
  description = "List of all bucket ARNs"
  value = [
    aws_s3_bucket.images.arn,
    aws_s3_bucket.videos.arn,
    aws_s3_bucket.webapp.arn,
  ]
}