# ============================================
# S3 Buckets Module
# ============================================
module "s3" {
  source = "./modules/s3"

  name_prefix              = local.name_prefix
  name_suffix              = local.name_suffix
  environment              = var.environment
  lifecycle_expiration_days = 30
}

# Deployment bucket for Lambda code (created separately to avoid circular deps)
resource "aws_s3_bucket" "deployment" {
  bucket = "${local.name_prefix}-deployment-${local.name_suffix}"

  tags = {
    Name        = "${local.name_prefix}-deployment"
    Environment = var.environment
  }
}

resource "aws_s3_bucket_versioning" "deployment" {
  bucket = aws_s3_bucket.deployment.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "deployment" {
  bucket = aws_s3_bucket.deployment.bucket

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "deployment" {
  bucket = aws_s3_bucket.deployment.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# ============================================
# DynamoDB Tables Module
# ============================================
module "dynamodb" {
  source = "./modules/dynamodb"

  name_prefix = local.name_prefix
  environment = var.environment
}

# ============================================
# Cognito Authentication Module
# ============================================
module "cognito" {
  source = "./modules/cognito"

  name_prefix   = local.name_prefix
  environment   = var.environment
  callback_urls = var.cognito_callback_urls
  logout_urls   = var.cognito_callback_urls  # Using same URLs for logout
}

# ============================================
# Secrets Manager Module
# ============================================
module "secrets" {
  source = "./modules/secrets"

  name_prefix = local.name_prefix
}

# ============================================
# ECR Repository for Lambda Container Images
# ============================================
resource "aws_ecr_repository" "lambda" {
  name                 = "${local.name_prefix}-lambda"
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }

  tags = {
    Name        = "${local.name_prefix}-lambda"
    Environment = var.environment
  }
}

resource "aws_ecr_lifecycle_policy" "lambda" {
  repository = aws_ecr_repository.lambda.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last 5 images"
        selection = {
          tagStatus   = "any"
          countType   = "imageCountMoreThan"
          countNumber = 5
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}

# ============================================
# Lambda Functions
# ============================================

# API Lambda function module
module "lambda_api" {
  source = "./modules/lambda"

  function_name = "${local.name_prefix}-api-handler"
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.lambda.repository_url}:latest"
  image_command = ["src.lambda_api.handler"]
  timeout       = var.lambda_timeout
  memory_size   = var.lambda_memory_size

  environment_variables = {
    # Database configuration
    DYNAMODB_USERS_TABLE    = module.dynamodb.users_table_name
    DYNAMODB_PRODUCTS_TABLE = module.dynamodb.products_table_name
    DYNAMODB_JOBS_TABLE     = module.dynamodb.jobs_table_name

    # Storage configuration
    S3_IMAGES_BUCKET = module.s3.images_bucket_name
    S3_VIDEOS_BUCKET = module.s3.videos_bucket_name

    # Auth configuration
    COGNITO_USER_POOL_ID = module.cognito.user_pool_id
    COGNITO_CLIENT_ID    = module.cognito.app_client_id
    COGNITO_REGION       = var.aws_region

    # Step Functions configuration (will be set via SSM)
    STEP_FUNCTIONS_STATE_MACHINE_ARN = module.stepfunctions.state_machine_arn

    # Frontend URL for CORS
    FRONTEND_URL = "https://${module.cloudfront.distribution_domain}"

    # Environment
    ENVIRONMENT  = var.environment
    PROJECT_NAME = var.project_name
  }

  depends_on = [aws_ecr_repository.lambda, module.cloudfront]
}

# Agents Lambda function module
module "lambda_agents" {
  source = "./modules/lambda"

  function_name = "${local.name_prefix}-agents-handler"
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.lambda.repository_url}:latest"
  image_command = ["src.lambda_agents.handler"]
  timeout       = var.agent_lambda_timeout
  memory_size   = var.lambda_memory_size

  environment_variables = {
    # API Keys (from Secrets Manager)
    SECRETS_OPENAI_KEY        = module.secrets.openai_secret_arn
    OPENAI_MODEL              = var.openai_model
    KLING_API_KEY_SECRET      = module.secrets.kling_secret_arn
    ELEVENLABS_API_KEY_SECRET = module.secrets.elevenlabs_secret_arn

    # Database configuration
    DYNAMODB_USERS_TABLE    = module.dynamodb.users_table_name
    DYNAMODB_PRODUCTS_TABLE = module.dynamodb.products_table_name
    DYNAMODB_JOBS_TABLE     = module.dynamodb.jobs_table_name

    # Storage configuration
    S3_IMAGES_BUCKET = module.s3.images_bucket_name
    S3_VIDEOS_BUCKET = module.s3.videos_bucket_name

    # Environment
    ENVIRONMENT  = var.environment
    PROJECT_NAME = var.project_name
  }

  depends_on = [aws_ecr_repository.lambda]
}

# TTS Lambda function module
module "lambda_tts" {
  source = "./modules/lambda"

  function_name = "${local.name_prefix}-tts-handler"
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.lambda.repository_url}:latest"
  image_command = ["src.lambda_tts.handler"]
  timeout       = 120  # TTS generation typically takes longer
  memory_size   = var.lambda_memory_size

  environment_variables = {
    # API Keys (from Secrets Manager)
    ELEVENLABS_API_KEY_SECRET = module.secrets.elevenlabs_secret_arn
    POLLY_REGION              = var.aws_region

    # Storage configuration
    S3_VIDEOS_BUCKET = module.s3.videos_bucket_name

    # Environment
    ENVIRONMENT  = var.environment
    PROJECT_NAME = var.project_name
  }

  depends_on = [aws_ecr_repository.lambda]
}

# Video Lambda function module
# Note: This Lambda is invoked BY Step Functions, so it doesn't need the ARN
module "lambda_video" {
  source = "./modules/lambda"

  function_name = "${local.name_prefix}-video-handler"
  package_type  = "Image"
  image_uri     = "${aws_ecr_repository.lambda.repository_url}:latest"
  image_command = ["src.lambda_video.handler"]
  timeout       = var.video_lambda_timeout
  memory_size   = var.lambda_memory_size

  environment_variables = {
    # API Keys (from Secrets Manager)
    KLING_API_KEY_SECRET   = module.secrets.kling_secret_arn
    SECRETS_DEEPINFRA_KEY  = module.secrets.deepinfra_secret_arn

    # Storage configuration
    S3_IMAGES_BUCKET = module.s3.images_bucket_name
    S3_VIDEOS_BUCKET = module.s3.videos_bucket_name

    # Environment
    ENVIRONMENT  = var.environment
    PROJECT_NAME = var.project_name
  }

  depends_on = [aws_ecr_repository.lambda]
}

# ============================================
# Additional IAM Policies for Lambda Functions
# ============================================

# API Lambda - Cognito permissions
resource "aws_iam_role_policy" "api_lambda_cognito" {
  name = "${local.name_prefix}-api-lambda-cognito-policy"
  role = module.lambda_api.role_name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "cognito-idp:SignUp",
          "cognito-idp:InitiateAuth",
          "cognito-idp:AdminConfirmSignUp",
          "cognito-idp:AdminGetUser"
        ]
        Resource = module.cognito.user_pool_arn
      }
    ]
  })
}

# API Lambda - DynamoDB permissions
resource "aws_iam_role_policy" "api_lambda_dynamodb" {
  name = "${local.name_prefix}-api-lambda-dynamodb-policy"
  role = module.lambda_api.role_name

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
          "dynamodb:Query",
          "dynamodb:Scan"
        ]
        Resource = [
          module.dynamodb.users_table_arn,
          module.dynamodb.products_table_arn,
          module.dynamodb.jobs_table_arn,
          "${module.dynamodb.users_table_arn}/index/*",
          "${module.dynamodb.products_table_arn}/index/*",
          "${module.dynamodb.jobs_table_arn}/index/*"
        ]
      }
    ]
  })
}

# API Lambda - S3 permissions
resource "aws_iam_role_policy" "api_lambda_s3" {
  name = "${local.name_prefix}-api-lambda-s3-policy"
  role = module.lambda_api.role_name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          module.s3.images_bucket_arn,
          "${module.s3.images_bucket_arn}/*",
          module.s3.videos_bucket_arn,
          "${module.s3.videos_bucket_arn}/*"
        ]
      }
    ]
  })
}

# API Lambda - Step Functions permissions
resource "aws_iam_role_policy" "api_lambda_stepfunctions" {
  name = "${local.name_prefix}-api-lambda-stepfunctions-policy"
  role = module.lambda_api.role_name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "states:StartExecution",
          "states:DescribeExecution",
          "states:StopExecution"
        ]
        Resource = module.stepfunctions.state_machine_arn
      }
    ]
  })

  depends_on = [module.stepfunctions]
}

# Agents Lambda - DynamoDB permissions
resource "aws_iam_role_policy" "agents_lambda_dynamodb" {
  name = "${local.name_prefix}-agents-lambda-dynamodb-policy"
  role = module.lambda_agents.role_name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:Query"
        ]
        Resource = [
          module.dynamodb.products_table_arn,
          module.dynamodb.jobs_table_arn,
          "${module.dynamodb.products_table_arn}/index/*",
          "${module.dynamodb.jobs_table_arn}/index/*"
        ]
      }
    ]
  })
}

# Agents Lambda - S3 permissions
resource "aws_iam_role_policy" "agents_lambda_s3" {
  name = "${local.name_prefix}-agents-lambda-s3-policy"
  role = module.lambda_agents.role_name

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
          "${module.s3.images_bucket_arn}/*",
          "${module.s3.videos_bucket_arn}/*"
        ]
      }
    ]
  })
}

# Agents Lambda - Secrets Manager permissions
resource "aws_iam_role_policy" "agents_lambda_secrets" {
  name = "${local.name_prefix}-agents-lambda-secrets-policy"
  role = module.lambda_agents.role_name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = [
          module.secrets.openai_secret_arn,
          module.secrets.kling_secret_arn,
          module.secrets.elevenlabs_secret_arn
        ]
      }
    ]
  })
}

# TTS Lambda - S3 permissions
resource "aws_iam_role_policy" "tts_lambda_s3" {
  name = "${local.name_prefix}-tts-lambda-s3-policy"
  role = module.lambda_tts.role_name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject"
        ]
        Resource = [
          "${module.s3.videos_bucket_arn}/*"
        ]
      }
    ]
  })
}

# TTS Lambda - Secrets Manager permissions
resource "aws_iam_role_policy" "tts_lambda_secrets" {
  name = "${local.name_prefix}-tts-lambda-secrets-policy"
  role = module.lambda_tts.role_name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = [
          module.secrets.elevenlabs_secret_arn
        ]
      }
    ]
  })
}

# TTS Lambda - Polly permissions
resource "aws_iam_role_policy" "tts_lambda_polly" {
  name = "${local.name_prefix}-tts-lambda-polly-policy"
  role = module.lambda_tts.role_name

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

# Video Lambda - S3 permissions
resource "aws_iam_role_policy" "video_lambda_s3" {
  name = "${local.name_prefix}-video-lambda-s3-policy"
  role = module.lambda_video.role_name

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
          "${module.s3.images_bucket_arn}/*",
          "${module.s3.videos_bucket_arn}/*"
        ]
      }
    ]
  })
}

# Video Lambda - Secrets Manager permissions
resource "aws_iam_role_policy" "video_lambda_secrets" {
  name = "${local.name_prefix}-video-lambda-secrets-policy"
  role = module.lambda_video.role_name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = [
          module.secrets.kling_secret_arn,
          module.secrets.deepinfra_secret_arn
        ]
      }
    ]
  })
}

# ============================================
# Step Functions Module
# ============================================
module "stepfunctions" {
  source = "./modules/stepfunctions"

  name_prefix      = local.name_prefix
  agent_lambda_arn = module.lambda_agents.function_arn
  tts_lambda_arn   = module.lambda_tts.function_arn
  video_lambda_arn = module.lambda_video.function_arn
}

# ============================================
# API Gateway Module
# ============================================
module "api_gateway" {
  source = "./modules/api_gateway"

  name_prefix          = local.name_prefix
  lambda_invoke_arn    = module.lambda_api.invoke_arn
  lambda_function_name = module.lambda_api.function_name
  cognito_user_pool_arn = module.cognito.user_pool_arn
  stage_name           = var.environment

  depends_on = [
    module.lambda_api,
    module.cognito
  ]
}

# ============================================
# CloudFront Module
# ============================================
module "cloudfront" {
  source = "./modules/cloudfront"

  name_prefix                    = local.name_prefix
  s3_bucket_id                   = module.s3.webapp_bucket_name
  s3_bucket_arn                  = module.s3.webapp_bucket_arn
  s3_bucket_regional_domain_name = "${module.s3.webapp_bucket_name}.s3.${var.aws_region}.amazonaws.com"

  depends_on = [module.s3]
}

# ============================================
# Monitoring Module
# ============================================
module "monitoring" {
  source = "./modules/monitoring"

  name_prefix           = local.name_prefix
  lambda_function_names = [
    module.lambda_api.function_name,
    module.lambda_agents.function_name,
    module.lambda_tts.function_name,
    module.lambda_video.function_name
  ]
  sns_email = var.budget_notification_email

  depends_on = [
    module.lambda_api,
    module.lambda_agents,
    module.lambda_tts,
    module.lambda_video
  ]
}

# ============================================
# Budget Module
# ============================================
module "budget" {
  source = "./modules/budget"

  name_prefix        = local.name_prefix
  environment        = var.environment
  budget_limit       = var.budget_limit
  notification_email = var.budget_notification_email

  depends_on = [
    module.s3,
    module.dynamodb
  ]
}
