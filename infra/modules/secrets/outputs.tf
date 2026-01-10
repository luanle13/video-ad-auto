output "anthropic_secret_arn" {
  description = "ARN of the Anthropic API key secret"
  value       = aws_secretsmanager_secret.anthropic.id
}

output "elevenlabs_secret_arn" {
  description = "ARN of the ElevenLabs API key secret"
  value       = aws_secretsmanager_secret.elevenlabs.id
}

output "kling_secret_arn" {
  description = "ARN of the Kling API key secret"
  value       = aws_secretsmanager_secret.kling.id
}

output "secret_arns" {
  description = "List of all secret ARNs"
  value = [
    aws_secretsmanager_secret.anthropic.id,
    aws_secretsmanager_secret.elevenlabs.id,
    aws_secretsmanager_secret.kling.id,
  ]
}