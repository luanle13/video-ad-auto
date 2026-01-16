output "state_machine_arn" {
  description = "ARN of the Step Functions state machine"
  value       = aws_sfn_state_machine.main.arn
}

output "state_machine_name" {
  description = "Name of the Step Functions state machine"
  value       = aws_sfn_state_machine.main.name
}

output "role_arn" {
  description = "ARN of the IAM role used by the state machine"
  value       = aws_iam_role.state_machine_role.arn
}