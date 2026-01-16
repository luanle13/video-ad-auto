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
# Lambda Functions
# ============================================

# API Lambda function module
module "lambda_api" {
  source = "./modules/lambda"

  function_name = "${local.name_prefix}-api-handler"
  handler       = "src.lambda_api.handler"
  runtime       = "python3.11"
  timeout       = var.lambda_timeout
  memory_size   = var.lambda_memory_size

  s3_bucket = aws_s3_bucket.deployment.bucket
  s3_key    = "lambdas/api-handler.zip"

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

    # Environment
    ENVIRONMENT  = var.environment
    PROJECT_NAME = var.project_name
  }

  layers = []
}

# Agents Lambda function module
module "lambda_agents" {
  source = "./modules/lambda"

  function_name = "${local.name_prefix}-agents-handler"
  handler       = "src.lambda_agents.handler"
  runtime       = "python3.11"
  timeout       = var.agent_lambda_timeout
  memory_size   = var.lambda_memory_size

  s3_bucket = aws_s3_bucket.deployment.bucket
  s3_key    = "lambdas/agents-handler.zip"

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

  layers = []
}

# TTS Lambda function module
module "lambda_tts" {
  source = "./modules/lambda"

  function_name = "${local.name_prefix}-tts-handler"
  handler       = "src.lambda_tts.handler"
  runtime       = "python3.11"
  timeout       = 120  # TTS generation typically takes longer
  memory_size   = var.lambda_memory_size

  s3_bucket = aws_s3_bucket.deployment.bucket
  s3_key    = "lambdas/tts-handler.zip"

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

  layers = []
}

# Video Lambda function module
# Note: This Lambda is invoked BY Step Functions, so it doesn't need the ARN
module "lambda_video" {
  source = "./modules/lambda"

  function_name = "${local.name_prefix}-video-handler"
  handler       = "src.lambda_video.handler"
  runtime       = "python3.11"
  timeout       = var.video_lambda_timeout
  memory_size   = var.lambda_memory_size

  s3_bucket = aws_s3_bucket.deployment.bucket
  s3_key    = "lambdas/video-handler.zip"

  environment_variables = {
    # API Keys (from Secrets Manager)
    KLING_API_KEY_SECRET = module.secrets.kling_secret_arn

    # Storage configuration
    S3_IMAGES_BUCKET = module.s3.images_bucket_name
    S3_VIDEOS_BUCKET = module.s3.videos_bucket_name

    # Environment
    ENVIRONMENT  = var.environment
    PROJECT_NAME = var.project_name
  }

  layers = []
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
