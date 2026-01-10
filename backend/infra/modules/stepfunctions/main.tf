# IAM role for Step Functions execution
resource "aws_iam_role" "state_machine_role" {
  name = "${var.name_prefix}-stepfunctions-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "states.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name        = "${var.name_prefix}-stepfunctions-role"
    Module      = "step-functions"
  }
}

# IAM policy for Step Functions role
resource "aws_iam_role_policy" "state_machine_policy" {
  name = "${var.name_prefix}-stepfunctions-policy"
  role = aws_iam_role.state_machine_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "lambda:InvokeFunction"
        ]
        Resource = [
          var.agent_lambda_arn,
          var.tts_lambda_arn,
          var.video_lambda_arn
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogDelivery",
          "logs:GetLogDelivery",
          "logs:UpdateLogDelivery",
          "logs:DeleteLogDelivery",
          "logs:ListLogDeliveries",
          "logs:PutResourcePolicy",
          "logs:DescribeResourcePolicies",
          "logs:DescribeLogGroups"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "xray:PutTraceSegments",
          "xray:PutTelemetryRecords",
          "xray:GetSamplingRules",
          "xray:GetSamplingTargets"
        ]
        Resource = "*"
      }
    ]
  })
}

resource "aws_sfn_state_machine" "main" {
  name     = "${var.name_prefix}-video-pipeline"
  role_arn = aws_iam_role.state_machine_role.arn

  definition = file("${path.module}/definition.json")

  tags = {
    Name        = "${var.name_prefix}-video-pipeline"
    Stage       = "production"  # Using a default since environment isn't defined in variables
    Module      = "step-functions"
  }

  depends_on = [aws_iam_role_policy.state_machine_policy]
}