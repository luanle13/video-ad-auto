output "monthly_budget_id" {
  description = "ID of the monthly budget"
  value       = aws_budgets_budget.monthly.id
}

output "monthly_budget_name" {
  description = "Name of the monthly budget"
  value       = aws_budgets_budget.monthly.name
}

output "lambda_budget_id" {
  description = "ID of the Lambda budget"
  value       = aws_budgets_budget.lambda.id
}

output "lambda_budget_name" {
  description = "Name of the Lambda budget"
  value       = aws_budgets_budget.lambda.name
}
