environment = "dev"
aws_region = "ap-southeast-1"
cognito_callback_urls = [
  "http://localhost:5173/callback",
  "http://localhost:3000/callback",
  "http://127.0.0.1:5173/callback",
  "http://127.0.0.1:3000/callback"
]
budget_limit = 100
budget_notification_email = "dev-team@example.com"
openai_model = "gpt-4o-mini"

# Azure OpenAI Configuration
# NOTE: Set azure_openai_api_key via environment variable TF_VAR_azure_openai_api_key
# or pass it via command line: terraform apply -var="azure_openai_api_key=YOUR_KEY"
azure_openai_api_key       = ""
azure_openai_endpoint      = "https://video-auto-ai-resource.openai.azure.com/openai/v1/"
azure_gpt_deployment_name  = "gpt-4.1"