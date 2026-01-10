# SNS Topic for alert notifications
resource "aws_sns_topic" "alerts" {
  name = "${var.name_prefix}-alerts-topic"

  tags = {
    Name        = "${var.name_prefix}-alerts-topic"
    Environment = "production"  # Using default since environment isn't in variables
    Module      = "monitoring"
  }
}

# SNS Topic Subscription for email alerts
resource "aws_sns_topic_subscription" "email_alerts" {
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.sns_email
}

# CloudWatch Alarm for Lambda function errors
resource "aws_cloudwatch_metric_alarm" "lambda_error_alarm" {
  for_each = toset(var.lambda_function_names)

  alarm_name          = "${var.name_prefix}-${each.value}-error-alarm"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = "300"  # 5 minutes
  statistic           = "Sum"
  threshold           = "1"
  alarm_description   = "Alarm when Lambda function ${each.value} has errors"

  dimensions = {
    FunctionName = each.value
  }

  alarm_actions = [
    aws_sns_topic.alerts.arn
  ]

  ok_actions = [
    aws_sns_topic.alerts.arn
  ]

  tags = {
    Name        = "${var.name_prefix}-${each.value}-error-alarm"
    Environment = "production"
    Module      = "monitoring"
  }
}

# CloudWatch Alarm for Lambda throttling
resource "aws_cloudwatch_metric_alarm" "lambda_throttles_alarm" {
  for_each = toset(var.lambda_function_names)

  alarm_name          = "${var.name_prefix}-${each.value}-throttles-alarm"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "1"
  metric_name         = "Throttles"
  namespace           = "AWS/Lambda"
  period              = "300"  # 5 minutes
  statistic           = "Sum"
  threshold           = "1"
  alarm_description   = "Alarm when Lambda function ${each.value} experiences throttling"

  dimensions = {
    FunctionName = each.value
  }

  alarm_actions = [
    aws_sns_topic.alerts.arn
  ]

  tags = {
    Name        = "${var.name_prefix}-${each.value}-throttles-alarm"
    Environment = "production"
    Module      = "monitoring"
  }
}

# CloudWatch Alarm for Lambda high duration
resource "aws_cloudwatch_metric_alarm" "lambda_duration_alarm" {
  for_each = toset(var.lambda_function_names)

  alarm_name          = "${var.name_prefix}-${each.value}-duration-alarm"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "3"
  metric_name         = "Duration"
  namespace           = "AWS/Lambda"
  period              = "300"  # 5 minutes
  statistic           = "Average"
  threshold           = "30000"  # 30 seconds average
  alarm_description   = "Alarm when Lambda function ${each.value} has high average duration"

  dimensions = {
    FunctionName = each.value
  }

  alarm_actions = [
    aws_sns_topic.alerts.arn
  ]

  tags = {
    Name        = "${var.name_prefix}-${each.value}-duration-alarm"
    Environment = "production"
    Module      = "monitoring"
  }
}