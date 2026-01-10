terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.30"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }

  backend "s3" {
    # Configuration provided via backend.hcl
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

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
    DYNAMODB_USERS_TABLE    = aws_dynamodb_table.users.name
    DYNAMODB_PRODUCTS_TABLE = aws_dynamodb_table.products.name
    DYNAMODB_JOBS_TABLE     = aws_dynamodb_table.jobs.name

    # Storage configuration
    S3_IMAGES_BUCKET = aws_s3_bucket.images.bucket
    S3_VIDEOS_BUCKET = aws_s3_bucket.videos.bucket

    # Auth configuration
    COGNITO_USER_POOL_ID     = aws_cognito_user_pool.main.id
    COGNITO_CLIENT_ID        = aws_cognito_user_pool_client.main.id
    COGNITO_REGION           = var.aws_region

    # Step Functions configuration
    STEP_FUNCTIONS_STATE_MACHINE_ARN = aws_sfn_state_machine.video_generation.arn

    # Environment
    ENVIRONMENT = var.environment
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
    ANTHROPIC_API_KEY_SECRET_NAME = aws_secretsmanager_secret.anthropic.name
    KLING_API_KEY_SECRET_NAME     = aws_secretsmanager_secret.kling.name
    ELEVENLABS_API_KEY_SECRET_NAME = aws_secretsmanager_secret.elevenlabs.name

    # Database configuration
    DYNAMODB_USERS_TABLE    = aws_dynamodb_table.users.name
    DYNAMODB_PRODUCTS_TABLE = aws_dynamodb_table.products.name
    DYNAMODB_JOBS_TABLE     = aws_dynamodb_table.jobs.name

    # Storage configuration
    S3_IMAGES_BUCKET = aws_s3_bucket.images.bucket
    S3_VIDEOS_BUCKET = aws_s3_bucket.videos.bucket

    # Environment
    ENVIRONMENT = var.environment
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
    ELEVENLABS_API_KEY_SECRET_NAME = aws_secretsmanager_secret.elevenlabs.name
    POLLY_REGION                   = var.aws_region

    # Storage configuration
    S3_VIDEOS_BUCKET = aws_s3_bucket.videos.bucket

    # Environment
    ENVIRONMENT = var.environment
    PROJECT_NAME = var.project_name
  }

  layers = []
}

# Video Lambda function module
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
    KLING_API_KEY_SECRET_NAME = aws_secretsmanager_secret.kling.name

    # Storage configuration
    S3_IMAGES_BUCKET = aws_s3_bucket.images.bucket
    S3_VIDEOS_BUCKET = aws_s3_bucket.videos.bucket

    # Step Functions configuration
    STEP_FUNCTIONS_STATE_MACHINE_ARN = aws_sfn_state_machine.video_generation.arn

    # Environment
    ENVIRONMENT = var.environment
    PROJECT_NAME = var.project_name
  }

  layers = []
}

# API Gateway module
module "api_gateway" {
  source = "./modules/api_gateway"

  name_prefix                  = local.name_prefix
  lambda_invoke_arn            = module.lambda_api.function_invoke_arn  # Assuming Lambda module outputs this
  lambda_function_name         = module.lambda_api.function_name
  cognito_user_pool_arn        = aws_cognito_user_pool.main.arn
  stage_name                   = var.environment

  depends_on = [
    module.lambda_api,
    aws_cognito_user_pool.main
  ]
}

# CloudFront module for static assets
module "cloudfront" {
  source = "./modules/cloudfront"

  name_prefix                        = local.name_prefix
  s3_bucket_id                       = aws_s3_bucket.webapp.id
  s3_bucket_arn                      = aws_s3_bucket.webapp.arn
  s3_bucket_regional_domain_name     = aws_s3_bucket.webapp.bucket_regional_domain_name

  depends_on = [
    aws_s3_bucket.webapp
  ]
}

# Monitoring module for Lambda function alerts
module "monitoring" {
  source = "./modules/monitoring"

  name_prefix            = local.name_prefix
  lambda_function_names  = [
    module.lambda_api.function_name,
    module.lambda_agents.function_name,
    module.lambda_tts.function_name,
    module.lambda_video.function_name
  ]
  sns_email              = var.notification_email

  depends_on = [
    module.lambda_api,
    module.lambda_agents,
    module.lambda_tts,
    module.lambda_video
  ]
}

# Budget module for cost monitoring
module "budget" {
  source = "./modules/budget"

  name_prefix        = local.name_prefix
  budget_limit       = var.monthly_budget_limit
  notification_email = var.notification_email

  depends_on = [
    aws_s3_bucket.videos,
    aws_s3_bucket.images,
    aws_dynamodb_table.users,
    aws_dynamodb_table.products,
    aws_dynamodb_table.jobs
  ]
}