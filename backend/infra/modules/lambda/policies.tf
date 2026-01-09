# Variables for ARNs used in IAM policies
variable "dynamodb_table_arns" {
  description = "List of DynamoDB table ARNs that the Lambda function needs access to"
  type        = list(string)
  default     = []
}

variable "s3_bucket_arns" {
  description = "List of S3 bucket ARNs that the Lambda function needs access to"
  type        = list(string)
  default     = []
}

variable "secrets_arns" {
  description = "List of Secrets Manager ARNs that the Lambda function needs access to"
  type        = list(string)
  default     = []
}

variable "sfn_arns" {
  description = "List of Step Functions ARNs that the Lambda function needs access to"
  type        = list(string)
  default     = []
}

variable "polly_access" {
  description = "Whether to grant Polly SynthesizeSpeech permission"
  type        = bool
  default     = false
}

# IAM policy for DynamoDB access
resource "aws_iam_role_policy" "dynamodb_access" {
  count  = length(var.dynamodb_table_arns) > 0 ? 1 : 0
  name   = "${var.function_name}-dynamodb-access"
  role   = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
          "dynamodb:Query"
        ]
        Resource = var.dynamodb_table_arns
      }
    ]
  })
}

# IAM policy for S3 access
resource "aws_iam_role_policy" "s3_access" {
  count  = length(var.s3_bucket_arns) > 0 ? 1 : 0
  name   = "${var.function_name}-s3-access"
  role   = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject"
        ]
        Resource = [
          for bucket_arn in var.s3_bucket_arns :
          "${bucket_arn}/*"
        ]
      }
    ]
  })
}

# IAM policy for Secrets Manager access
resource "aws_iam_role_policy" "secrets_access" {
  count  = length(var.secrets_arns) > 0 ? 1 : 0
  name   = "${var.function_name}-secrets-access"
  role   = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = var.secrets_arns
      }
    ]
  })
}

# IAM policy for Step Functions access
resource "aws_iam_role_policy" "sfn_access" {
  count  = length(var.sfn_arns) > 0 ? 1 : 0
  name   = "${var.function_name}-sfn-access"
  role   = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "states:StartExecution"
        ]
        Resource = var.sfn_arns
      }
    ]
  })
}

# Conditional IAM policy for Polly access
resource "aws_iam_role_policy" "polly_access" {
  count  = var.polly_access ? 1 : 0
  name   = "${var.function_name}-polly-access"
  role   = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "polly:SynthesizeSpeech"
        ]
        Resource = "*"
      }
    ]
  })
}