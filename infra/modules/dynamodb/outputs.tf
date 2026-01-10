output "users_table_name" {
  description = "Name of the users table"
  value       = aws_dynamodb_table.users.name
}

output "users_table_arn" {
  description = "ARN of the users table"
  value       = aws_dynamodb_table.users.arn
}

output "products_table_name" {
  description = "Name of the products table"
  value       = aws_dynamodb_table.products.name
}

output "products_table_arn" {
  description = "ARN of the products table"
  value       = aws_dynamodb_table.products.arn
}

output "jobs_table_name" {
  description = "Name of the jobs table"
  value       = aws_dynamodb_table.jobs.name
}

output "jobs_table_arn" {
  description = "ARN of the jobs table"
  value       = aws_dynamodb_table.jobs.arn
}

output "table_arns" {
  description = "List of all table ARNs"
  value = [
    aws_dynamodb_table.users.arn,
    aws_dynamodb_table.products.arn,
    aws_dynamodb_table.jobs.arn,
  ]
}