output "api_id" {
  description = "ID of the API Gateway REST API"
  value       = aws_api_gateway_rest_api.main.id
}

output "api_endpoint" {
  description = "Full URL of the API Gateway endpoint"
  value       = aws_api_gateway_deployment.main.invoke_url
}

output "stage_name" {
  description = "Name of the API Gateway stage"
  value       = var.stage_name
}