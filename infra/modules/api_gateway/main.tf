resource "aws_api_gateway_rest_api" "main" {
  name        = "${var.name_prefix}-api"
  description = "API Gateway for AI Video Automation System"

  endpoint_configuration {
    types = ["REGIONAL"]  # Regional endpoint for lower latency in ap-southeast-1
  }

  tags = {
    Name        = "${var.name_prefix}-api"
    Stage       = var.stage_name
    Module      = "api-gateway"
  }
}

# Cognito Authorizer for API Gateway
resource "aws_api_gateway_authorizer" "cognito" {
  name          = "cognito"
  rest_api_id   = aws_api_gateway_rest_api.main.id
  type          = "COGNITO_USER_POOLS"
  provider_arns = [var.cognito_user_pool_arn]
}

# Proxy resource to catch all paths
resource "aws_api_gateway_resource" "proxy" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_rest_api.main.root_resource_id
  path_part   = "{proxy+}"
}

# ANY method for proxy resource with Cognito authorizer
resource "aws_api_gateway_method" "proxy_any" {
  rest_api_id      = aws_api_gateway_rest_api.main.id
  resource_id      = aws_api_gateway_resource.proxy.id
  http_method      = "ANY"
  authorization    = "COGNITO_USER_POOLS"  # Use Cognito authorizer
  authorizer_id    = aws_api_gateway_authorizer.cognito.id

  depends_on = [aws_api_gateway_authorizer.cognito]
}

# AWS_PROXY integration for proxy resource
resource "aws_api_gateway_integration" "proxy_int" {
  rest_api_id             = aws_api_gateway_rest_api.main.id
  resource_id             = aws_api_gateway_resource.proxy.id
  http_method             = aws_api_gateway_method.proxy_any.http_method
  type                    = "AWS_PROXY"
  uri                     = var.lambda_invoke_arn  # Points to Lambda function
  integration_http_method = "POST"
  passthrough_behavior    = "WHEN_NO_MATCH"  # Pass through requests that don't match specific integrations

  depends_on = [aws_api_gateway_method.proxy_any]
}

# Health check resource (no authentication required)
resource "aws_api_gateway_resource" "health" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_rest_api.main.root_resource_id
  path_part   = "health"
}

# GET method for health endpoint (no auth)
resource "aws_api_gateway_method" "health_get" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.health.id
  http_method   = "GET"
  authorization = "NONE"  # No authentication for health check
}

# AWS_PROXY integration for health endpoint
resource "aws_api_gateway_integration" "health_int" {
  rest_api_id             = aws_api_gateway_rest_api.main.id
  resource_id             = aws_api_gateway_resource.health.id
  http_method             = aws_api_gateway_method.health_get.http_method
  type                    = "AWS_PROXY"
  uri                     = var.lambda_invoke_arn  # Points to Lambda function
  integration_http_method = "POST"

  depends_on = [aws_api_gateway_method.health_get]
}

# Deployment resource
resource "aws_api_gateway_deployment" "main" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  stage_name  = var.stage_name  # Use stage name from variables

  # Trigger redeployment when resources change
  triggers = {
    redeployment = sha1(jsonencode([
      aws_api_gateway_method.proxy_any.id,
      aws_api_gateway_integration.proxy_int.id,
      aws_api_gateway_method.health_get.id,
      aws_api_gateway_integration.health_int.id,
    ]))
  }

  depends_on = [
    aws_api_gateway_integration.proxy_int,
    aws_api_gateway_integration.health_int,
  ]
}

# Stage resource
resource "aws_api_gateway_stage" "main" {
  stage_name    = var.stage_name
  rest_api_id   = aws_api_gateway_rest_api.main.id
  deployment_id = aws_api_gateway_deployment.main.id

  # Enable detailed metrics for monitoring
  xray_tracing_enabled = true

  # Access log settings
  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api_access_logs.arn
    format = jsonencode({
      requestId      = "$context.requestId"
      ip             = "$context.identity.sourceIp"
      caller         = "$context.identity.caller"
      userAgent      = "$context.identity.userAgent"
      requestTime    = "$context.requestTime"
      httpMethod     = "$context.httpMethod"
      resourcePath   = "$context.resourcePath"
      status         = "$context.status"
      protocol       = "$context.protocol"
      responseLength = "$context.responseLength"
    })
  }

  # Throttling settings
  variables = {
    throttling_burst_limit = 5000
    throttling_rate_limit  = 10000
  }

  tags = {
    Name        = "${var.name_prefix}-${var.stage_name}"
    Stage       = var.stage_name
    Module      = "api-gateway-stage"
  }
}

# CloudWatch log group for API access logs
resource "aws_cloudwatch_log_group" "api_access_logs" {
  name              = "/aws/api-gateway/${var.name_prefix}-access-logs"
  retention_in_days = 30

  tags = {
    Name        = "${var.name_prefix}-access-logs"
    Stage       = var.stage_name
    Module      = "api-gateway"
  }
}

# Lambda permission to allow API Gateway to invoke Lambda function
resource "aws_lambda_permission" "api_gateway" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = var.lambda_function_name  # Use function name from variables
  principal     = "apigateway.amazonaws.com"

  # Source ARN includes the execute-api endpoint
  source_arn = "${aws_api_gateway_rest_api.main.execution_arn}/*/*/*"
}