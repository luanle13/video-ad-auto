resource "aws_lambda_function" "main" {
  function_name = var.function_name

  role = aws_iam_role.lambda_role.arn

  handler = var.handler
  runtime = var.runtime
  timeout = var.timeout
  memory_size = var.memory_size

  s3_bucket = var.s3_bucket
  s3_key    = var.s3_key

  architectures = ["arm64"]

  environment {
    variables = var.environment_variables
  }

  tracing_config {
    mode = "Active"
  }

  layers = var.layers

  dynamic "vpc_config" {
    for_each = var.vpc_config != null ? [var.vpc_config] : []
    content {
      subnet_ids         = vpc_config.value.subnet_ids
      security_group_ids = vpc_config.value.security_group_ids
    }
  }

  tags = {
    Name        = var.function_name
    Module      = "lambda"
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