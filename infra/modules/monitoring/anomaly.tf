# Cost Explorer Anomaly Monitors - DISABLED
# These resources require Cost Explorer to be enabled at the AWS account level.
# To enable: AWS Console > Billing > Cost Explorer > Enable Cost Explorer
# Once enabled, uncomment the resources below.

# Note: Cost Explorer requires account-level activation and has its own pricing.
# After enabling, wait 24 hours for data to become available before creating monitors.

/*
# Cost Anomaly Monitor - Detects unusual spending patterns by service
resource "aws_ce_anomaly_monitor" "main" {
  name              = "${var.name_prefix}-cost-monitor"
  monitor_type      = "DIMENSIONAL"
  monitor_dimension = "SERVICE"

  tags = {
    Name   = "${var.name_prefix}-cost-monitor"
    Module = "monitoring"
  }
}

# Cost Anomaly Subscription - Sends alerts when anomalies are detected
resource "aws_ce_anomaly_subscription" "main" {
  name      = "${var.name_prefix}-anomaly-alerts"
  frequency = "DAILY"

  monitor_arn_list = [
    aws_ce_anomaly_monitor.main.arn
  ]

  subscriber {
    type    = "EMAIL"
    address = var.sns_email
  }

  # Alert if cost is 10% or more above expected
  threshold_expression {
    dimension {
      key           = "ANOMALY_TOTAL_IMPACT_PERCENTAGE"
      values        = ["10"]
      match_options = ["GREATER_THAN_OR_EQUAL"]
    }
  }

  tags = {
    Name   = "${var.name_prefix}-anomaly-alerts"
    Module = "monitoring"
  }
}

# Additional monitor for Lambda specifically (primary cost driver)
resource "aws_ce_anomaly_monitor" "lambda" {
  name         = "${var.name_prefix}-lambda-cost-monitor"
  monitor_type = "CUSTOM"

  monitor_specification = jsonencode({
    And = null
    Or  = null
    Not = null
    Dimensions = {
      Key          = "SERVICE"
      Values       = ["AWS Lambda"]
      MatchOptions = null
    }
    CostCategories = null
    Tags           = null
  })

  tags = {
    Name   = "${var.name_prefix}-lambda-cost-monitor"
    Module = "monitoring"
  }
}

# Subscription for Lambda-specific anomalies with lower threshold
resource "aws_ce_anomaly_subscription" "lambda" {
  name      = "${var.name_prefix}-lambda-anomaly-alerts"
  frequency = "IMMEDIATE"

  monitor_arn_list = [
    aws_ce_anomaly_monitor.lambda.arn
  ]

  subscriber {
    type    = "EMAIL"
    address = var.sns_email
  }

  # Alert immediately if Lambda cost spikes 20% above expected
  threshold_expression {
    dimension {
      key           = "ANOMALY_TOTAL_IMPACT_PERCENTAGE"
      values        = ["20"]
      match_options = ["GREATER_THAN_OR_EQUAL"]
    }
  }

  tags = {
    Name   = "${var.name_prefix}-lambda-anomaly-alerts"
    Module = "monitoring"
  }
}
*/
