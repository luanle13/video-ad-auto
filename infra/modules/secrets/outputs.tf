output "openai_secret_arn" {
  description = "ARN of the OpenAI API key secret"
  value       = aws_secretsmanager_secret.openai.arn
}

output "elevenlabs_secret_arn" {
  description = "ARN of the ElevenLabs API key secret"
  value       = aws_secretsmanager_secret.elevenlabs.arn
}

output "kling_secret_arn" {
  description = "ARN of the Kling API key secret"
  value       = aws_secretsmanager_secret.kling.arn
}

output "deepinfra_secret_arn" {
  description = "ARN of the DeepInfra API key secret"
  value       = aws_secretsmanager_secret.deepinfra.arn
}

output "azure_openai_secret_arn" {
  description = "ARN of the Azure OpenAI API key secret"
  value       = aws_secretsmanager_secret.azure_openai.arn
}

output "secret_arns" {
  description = "List of all secret ARNs"
  value = [
    aws_secretsmanager_secret.openai.arn,
    aws_secretsmanager_secret.elevenlabs.arn,
    aws_secretsmanager_secret.kling.arn,
    aws_secretsmanager_secret.deepinfra.arn,
    aws_secretsmanager_secret.azure_openai.arn,
  ]
}