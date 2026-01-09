resource "aws_secretsmanager_secret" "anthropic" {
  name = "${var.name_prefix}/anthropic-api-key"

  description = "Anthropic API key for Claude 3.5 Sonnet"

  # Add tags for identification
  tags = {
    Name        = "${var.name_prefix}-anthropic-api-key"
    Module      = "secrets"
    Service     = "anthropic"
  }

  # Secret value will be populated manually after deployment
}

resource "aws_secretsmanager_secret" "elevenlabs" {
  name = "${var.name_prefix}/elevenlabs-api-key"

  description = "ElevenLabs API key for TTS service"

  # Add tags for identification
  tags = {
    Name        = "${var.name_prefix}-elevenlabs-api-key"
    Module      = "secrets"
    Service     = "elevenlabs"
  }

  # Secret value will be populated manually after deployment
}

resource "aws_secretsmanager_secret" "kling" {
  name = "${var.name_prefix}/kling-api-key"

  description = "Kling AI API key for video generation"

  # Add tags for identification
  tags = {
    Name        = "${var.name_prefix}-kling-api-key"
    Module      = "secrets"
    Service     = "kling"
  }

  # Secret value will be populated manually after deployment
}