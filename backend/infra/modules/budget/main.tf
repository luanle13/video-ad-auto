# AWS Budget for cost monitoring
resource "aws_budgets_budget" "monthly_cost_budget" {
  name              = "${var.name_prefix}-monthly-budget"
  budget_type       = "COST"
  limit_amount      = var.budget_limit
  limit_unit        = "USD"
  time_unit         = "MONTHLY"
  account_id        = data.aws_caller_identity.current.account_id

  # Cost filters to scope the budget to specific services/resources if needed
  # For now, applying to entire account
  cost_filters = {
    # Limit to specific services if needed
    # "Service" = "AmazonApiGateway,AmazonS3,AmazonDynamoDB,AWSLambda"
  }

  # Notifications for budget thresholds
  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 50.0  # 50% of budget
    threshold_type             = "PERCENTAGE"
    notification_type          = "FORECASTED"
    subscriber_email_addresses = [var.notification_email]
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 80.0  # 80% of budget
    threshold_type             = "PERCENTAGE"
    notification_type          = "FORECASTED"
    subscriber_email_addresses = [var.notification_email]
  }

  notification {
    comparison_operator        = "EQUAL_TO"
    threshold                  = 100.0  # 100% of budget (reached limit)
    threshold_type             = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = [var.notification_email]
  }

  # Additional notification for actual spend reaching 100%
  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 100.0  # Over budget
    threshold_type             = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = [var.notification_email]
  }

  tags = {
    Name        = "${var.name_prefix}-monthly-budget"
    Environment = "production"  # Using default since environment isn't in variables
    Module      = "budget"
  }
}

# Data source to get current AWS account ID
data "aws_caller_identity" "current" {}