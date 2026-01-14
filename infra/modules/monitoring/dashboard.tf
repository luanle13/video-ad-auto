# CloudWatch Dashboard for cost and performance monitoring
resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = "${var.name_prefix}-dashboard"

  dashboard_body = jsonencode({
    widgets = [
      # Row 1: Lambda Invocations and Errors
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
      },
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
      },

      # Row 2: Lambda Duration and Throttles
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
      },
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
      },

      # Row 3: Lambda Concurrent Executions and Memory
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
      },
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
      },

      # Row 4: DynamoDB Consumed Capacity
      {
        type   = "metric"
        x      = 0
        y      = 18
        width  = 12
        height = 6
        properties = {
          title  = "DynamoDB Read Capacity"
          region = var.aws_region
          stat   = "Sum"
          period = 300
          metrics = [
            for table in var.dynamodb_table_names : ["AWS/DynamoDB", "ConsumedReadCapacityUnits", "TableName", table]
          ]
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 18
        width  = 12
        height = 6
        properties = {
          title  = "DynamoDB Write Capacity"
          region = var.aws_region
          stat   = "Sum"
          period = 300
          metrics = [
            for table in var.dynamodb_table_names : ["AWS/DynamoDB", "ConsumedWriteCapacityUnits", "TableName", table]
          ]
        }
      },

      # Row 5: DynamoDB Throttles and Errors
      {
        type   = "metric"
        x      = 0
        y      = 24
        width  = 12
        height = 6
        properties = {
          title  = "DynamoDB Throttled Requests"
          region = var.aws_region
          stat   = "Sum"
          period = 300
          metrics = [
            for table in var.dynamodb_table_names : ["AWS/DynamoDB", "ThrottledRequests", "TableName", table]
          ]
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 24
        width  = 12
        height = 6
        properties = {
          title  = "DynamoDB User Errors"
          region = var.aws_region
          stat   = "Sum"
          period = 300
          metrics = [
            for table in var.dynamodb_table_names : ["AWS/DynamoDB", "UserErrors", "TableName", table]
          ]
        }
      },

      # Row 6: API Gateway
      {
        type   = "metric"
        x      = 0
        y      = 30
        width  = 8
        height = 6
        properties = {
          title  = "API Gateway Requests"
          region = var.aws_region
          stat   = "Sum"
          period = 300
          metrics = [
            ["AWS/ApiGateway", "Count", "ApiName", var.api_gateway_name]
          ]
        }
      },
      {
        type   = "metric"
        x      = 8
        y      = 30
        width  = 8
        height = 6
        properties = {
          title  = "API Gateway Latency (ms)"
          region = var.aws_region
          stat   = "Average"
          period = 300
          metrics = [
            ["AWS/ApiGateway", "Latency", "ApiName", var.api_gateway_name]
          ]
        }
      },
      {
        type   = "metric"
        x      = 16
        y      = 30
        width  = 8
        height = 6
        properties = {
          title  = "API Gateway 4xx/5xx Errors"
          region = var.aws_region
          stat   = "Sum"
          period = 300
          metrics = [
            ["AWS/ApiGateway", "4XXError", "ApiName", var.api_gateway_name],
            ["AWS/ApiGateway", "5XXError", "ApiName", var.api_gateway_name]
          ]
        }
      },

      # Row 7: S3 Storage
      {
        type   = "metric"
        x      = 0
        y      = 36
        width  = 12
        height = 6
        properties = {
          title  = "S3 Bucket Size (Bytes)"
          region = var.aws_region
          stat   = "Average"
          period = 86400
          metrics = [
            for bucket in var.s3_bucket_names : ["AWS/S3", "BucketSizeBytes", "BucketName", bucket, "StorageType", "StandardStorage"]
          ]
        }
      },
      {
        type   = "metric"
        x      = 12
        y      = 36
        width  = 12
        height = 6
        properties = {
          title  = "S3 Number of Objects"
          region = var.aws_region
          stat   = "Average"
          period = 86400
          metrics = [
            for bucket in var.s3_bucket_names : ["AWS/S3", "NumberOfObjects", "BucketName", bucket, "StorageType", "AllStorageTypes"]
          ]
        }
      },

      # Row 8: Step Functions
      {
        type   = "metric"
        x      = 0
        y      = 42
        width  = 8
        height = 6
        properties = {
          title  = "Step Functions Executions Started"
          region = var.aws_region
          stat   = "Sum"
          period = 300
          metrics = [
            ["AWS/States", "ExecutionsStarted", "StateMachineArn", var.step_function_arn]
          ]
        }
      },
      {
        type   = "metric"
        x      = 8
        y      = 42
        width  = 8
        height = 6
        properties = {
          title  = "Step Functions Executions Succeeded"
          region = var.aws_region
          stat   = "Sum"
          period = 300
          metrics = [
            ["AWS/States", "ExecutionsSucceeded", "StateMachineArn", var.step_function_arn]
          ]
        }
      },
      {
        type   = "metric"
        x      = 16
        y      = 42
        width  = 8
        height = 6
        properties = {
          title  = "Step Functions Executions Failed"
          region = var.aws_region
          stat   = "Sum"
          period = 300
          metrics = [
            ["AWS/States", "ExecutionsFailed", "StateMachineArn", var.step_function_arn]
          ]
        }
      }
    ]
  })
}
