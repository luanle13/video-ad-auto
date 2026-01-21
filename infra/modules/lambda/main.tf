resource "aws_lambda_function" "main" {
  function_name = var.function_name

  role = aws_iam_role.lambda_role.arn

  # For Zip deployments
  handler = var.package_type == "Zip" ? var.handler : null
  runtime = var.package_type == "Zip" ? var.runtime : null

  # Package type (Zip or Image)
  package_type = var.package_type

  # For Zip deployments - S3
  s3_bucket = var.package_type == "Zip" ? var.s3_bucket : null
  s3_key    = var.package_type == "Zip" ? var.s3_key : null

  # For Image deployments - ECR
  image_uri = var.package_type == "Image" ? var.image_uri : null

  timeout     = var.timeout
  memory_size = var.memory_size

  architectures = ["arm64"]

  environment {
    variables = var.environment_variables
  }

  tracing_config {
    mode = "Active"
  }

  layers = var.package_type == "Zip" ? var.layers : []

  # For Image deployments - override CMD to set handler
  dynamic "image_config" {
    for_each = var.package_type == "Image" && var.image_command != null ? [1] : []
    content {
      command = var.image_command
    }
  }

  dynamic "vpc_config" {
    for_each = var.vpc_config != null ? [var.vpc_config] : []
    content {
      subnet_ids         = vpc_config.value.subnet_ids
      security_group_ids = vpc_config.value.security_group_ids
    }
  }

  tags = {
    Name   = var.function_name
    Module = "lambda"
  }
}

resource "aws_cloudwatch_log_group" "lambda_log_group" {
  name              = "/aws/lambda/${var.function_name}"
  retention_in_days = 30

  tags = {
    Name        = "${var.function_name}-log-group"
    Module      = "lambda"
  }
}