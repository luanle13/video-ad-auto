# CloudWatch Dashboard for Lambda monitoring
resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = "${var.name_prefix}-dashboard"

  dashboard_body = jsonencode({
    widgets = concat(
      # Lambda Invocations
      [
        {
          type   = "metric"
          x      = 0
          y      = 0
          width  = 12
          height = 6
          properties = {
            title  = "Lambda Invocations"
            region = var.aws_region
            stat   = "Sum"
            period = 300
            metrics = [
              for fn in var.lambda_function_names : ["AWS/Lambda", "Invocations", "FunctionName", fn]
            ]
          }
        }
      ],
      # Lambda Errors
      [
        {
          type   = "metric"
          x      = 12
          y      = 0
          width  = 12
          height = 6
          properties = {
            title  = "Lambda Errors"
            region = var.aws_region
            stat   = "Sum"
            period = 300
            metrics = [
              for fn in var.lambda_function_names : ["AWS/Lambda", "Errors", "FunctionName", fn]
            ]
          }
        }
      ],
      # Lambda Duration
      [
        {
          type   = "metric"
          x      = 0
          y      = 6
          width  = 12
          height = 6
          properties = {
            title  = "Lambda Duration (Avg ms)"
            region = var.aws_region
            stat   = "Average"
            period = 300
            metrics = [
              for fn in var.lambda_function_names : ["AWS/Lambda", "Duration", "FunctionName", fn]
            ]
          }
        }
      ],
      # Lambda Throttles
      [
        {
          type   = "metric"
          x      = 12
          y      = 6
          width  = 12
          height = 6
          properties = {
            title  = "Lambda Throttles"
            region = var.aws_region
            stat   = "Sum"
            period = 300
            metrics = [
              for fn in var.lambda_function_names : ["AWS/Lambda", "Throttles", "FunctionName", fn]
            ]
          }
        }
      ],
      # Lambda Concurrent Executions
      [
        {
          type   = "metric"
          x      = 0
          y      = 12
          width  = 12
          height = 6
          properties = {
            title  = "Lambda Concurrent Executions"
            region = var.aws_region
            stat   = "Maximum"
            period = 300
            metrics = [
              for fn in var.lambda_function_names : ["AWS/Lambda", "ConcurrentExecutions", "FunctionName", fn]
            ]
          }
        }
      ],
      # Lambda Duration P95
      [
        {
          type   = "metric"
          x      = 12
          y      = 12
          width  = 12
          height = 6
          properties = {
            title  = "Lambda Duration (P95 ms)"
            region = var.aws_region
            stat   = "p95"
            period = 300
            metrics = [
              for fn in var.lambda_function_names : ["AWS/Lambda", "Duration", "FunctionName", fn]
            ]
          }
        }
      ]
    )
  })
}
