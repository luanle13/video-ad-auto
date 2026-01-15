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