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

# ANY method for proxy resource - Lambda handles authentication
resource "aws_api_gateway_method" "proxy_any" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.proxy.id
  http_method   = "ANY"
  authorization = "NONE"  # Lambda handles auth validation for access tokens
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

# Auth resource (no authentication required for register/login)
resource "aws_api_gateway_resource" "auth" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_rest_api.main.root_resource_id
  path_part   = "auth"
}

# Auth proxy resource to catch all auth paths (register, login, etc.)
resource "aws_api_gateway_resource" "auth_proxy" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  parent_id   = aws_api_gateway_resource.auth.id
  path_part   = "{proxy+}"
}

# ANY method for auth proxy (no authentication)
resource "aws_api_gateway_method" "auth_any" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.auth_proxy.id
  http_method   = "ANY"
  authorization = "NONE"  # No authentication for auth endpoints
}

# AWS_PROXY integration for auth endpoints
resource "aws_api_gateway_integration" "auth_int" {
  rest_api_id             = aws_api_gateway_rest_api.main.id
  resource_id             = aws_api_gateway_resource.auth_proxy.id
  http_method             = aws_api_gateway_method.auth_any.http_method
  type                    = "AWS_PROXY"
  uri                     = var.lambda_invoke_arn
  integration_http_method = "POST"

  depends_on = [aws_api_gateway_method.auth_any]
}

# CORS support for auth endpoints
resource "aws_api_gateway_method" "auth_options" {
  rest_api_id   = aws_api_gateway_rest_api.main.id
  resource_id   = aws_api_gateway_resource.auth_proxy.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "auth_options_int" {
  rest_api_id             = aws_api_gateway_rest_api.main.id
  resource_id             = aws_api_gateway_resource.auth_proxy.id
  http_method             = aws_api_gateway_method.auth_options.http_method
  type                    = "MOCK"
  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_method_response" "auth_options_200" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.auth_proxy.id
  http_method = aws_api_gateway_method.auth_options.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }
}

resource "aws_api_gateway_integration_response" "auth_options_int_response" {
  rest_api_id = aws_api_gateway_rest_api.main.id
  resource_id = aws_api_gateway_resource.auth_proxy.id
  http_method = aws_api_gateway_method.auth_options.http_method
  status_code = aws_api_gateway_method_response.auth_options_200.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,POST,PUT,DELETE,OPTIONS'"
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
  }
}

# Deployment resource
resource "aws_api_gateway_deployment" "main" {
  rest_api_id = aws_api_gateway_rest_api.main.id

  # Trigger redeployment when resources change
  triggers = {
    redeployment = sha1(jsonencode([
      aws_api_gateway_method.proxy_any.id,
      aws_api_gateway_integration.proxy_int.id,
      aws_api_gateway_method.health_get.id,
      aws_api_gateway_integration.health_int.id,
      aws_api_gateway_method.auth_any.id,
      aws_api_gateway_integration.auth_int.id,
    ]))
  }

  depends_on = [
    aws_api_gateway_integration.proxy_int,
    aws_api_gateway_integration.health_int,
    aws_api_gateway_integration.auth_int,
    aws_api_gateway_integration_response.auth_options_int_response,
  ]

  lifecycle {
    create_before_destroy = true
  }
}

# Stage resource
resource "aws_api_gateway_stage" "main" {
  stage_name    = var.stage_name
  rest_api_id   = aws_api_gateway_rest_api.main.id
  deployment_id = aws_api_gateway_deployment.main.id

  # Enable X-Ray tracing for monitoring
  xray_tracing_enabled = true

  # Note: Access logging requires CloudWatch Logs role to be set at account level
  # AWS Console > API Gateway > Settings > CloudWatch log role ARN
  # Once configured, uncomment access_log_settings below

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