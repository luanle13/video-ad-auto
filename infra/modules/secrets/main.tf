resource "aws_secretsmanager_secret" "openai" {
  name        = "${var.name_prefix}/openai-api-key"
  description = "OpenAI API key"

  tags = {
    Name    = "${var.name_prefix}-openai-api-key"
    Module  = "secrets"
    Service = "openai"
  }
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