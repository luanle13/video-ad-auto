resource "aws_sfn_state_machine" "main" {
  name     = "${var.name_prefix}-video-pipeline"
  role_arn = aws_iam_role.state_machine_role.arn

  definition = file("${path.module}/definition.json")

  tags = {
    Name        = "${var.name_prefix}-video-pipeline"
    Stage       = "production"  # Using a default since environment isn't defined in variables
    Module      = "step-functions"
  }

  depends_on = [aws_iam_role.state_machine_role]
}