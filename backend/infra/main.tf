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