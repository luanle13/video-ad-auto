resource "aws_cognito_user_pool" "main" {
  name = "${var.name_prefix}-users"

  # Use email as username
  username_attributes = ["email"]

  # Auto-verify email addresses
  auto_verified_attributes = ["email"]

  # Password policy
  password_policy {
    minimum_length    = 8
    require_lowercase = true
    require_numbers   = true
    require_symbols   = false  # Not required per requirements
    require_uppercase = true
  }

  # Account recovery settings
  account_recovery_setting {
    recovery_mechanism {
      name      = "verified_email"
      priority  = 1
    }
  }

  # Add tags for identification
  tags = {
    Name        = "${var.name_prefix}-users"
    Environment = var.environment
    Module      = "cognito"
  }
}

resource "aws_cognito_user_pool_client" "main" {
  name = "${var.name_prefix}-web-client"

  # Reference the user pool
  user_pool_id = aws_cognito_user_pool.main.id

  # Don't generate a client secret (for web apps)
  generate_secret = false

  # Supported identity providers
  supported_identity_providers = ["COGNITO"]

  # Explicit auth flows
  explicit_auth_flows = [
    "USER_PASSWORD_AUTH",
    "REFRESH_TOKEN_AUTH"
  ]

  # Callback and logout URLs from variables
  callback_urls = var.callback_urls
  logout_urls   = var.logout_urls

  # Access token validity (in minutes)
  access_token_validity = 60

  # ID token validity (in minutes)
  id_token_validity = 60

  # Refresh token validity (in days)
  refresh_token_validity = 30

  # Token validity units
  access_token_validity_unit  = "minutes"
  id_token_validity_unit      = "minutes"
  refresh_token_validity_unit = "days"

  # Prevent user existence errors
  prevent_user_existence_errors = "ENABLED"

  # Add tags for identification
  tags = {
    Name        = "${var.name_prefix}-web-client"
    Environment = var.environment
    Module      = "cognito"
  }
}