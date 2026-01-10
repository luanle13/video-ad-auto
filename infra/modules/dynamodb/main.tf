resource "aws_dynamodb_table" "users" {
  name         = "${var.name_prefix}-users"
  billing_mode = "PAY_PER_REQUEST"

  # Primary key
  hash_key = "user_id"

  # Table attributes
  attribute {
    name = "user_id"
    type = "S"  # String
  }

  attribute {
    name = "email"
    type = "S"  # String
  }

  # Global Secondary Index for email lookups
  global_secondary_index {
    name            = "email-index"
    hash_key        = "email"
    projection_type = "ALL"
  }

  # Add tags for identification
  tags = {
    Name        = "${var.name_prefix}-users"
    Environment = var.environment
    Module      = "dynamodb"
  }
}

resource "aws_dynamodb_table" "products" {
  name         = "${var.name_prefix}-products"
  billing_mode = "PAY_PER_REQUEST"

  # Primary key (composite)
  hash_key  = "user_id"
  range_key = "product_id"

  # Table attributes
  attribute {
    name = "user_id"
    type = "S"  # String
  }

  attribute {
    name = "product_id"
    type = "S"  # String
  }

  # Add tags for identification
  tags = {
    Name        = "${var.name_prefix}-products"
    Environment = var.environment
    Module      = "dynamodb"
  }
}

resource "aws_dynamodb_table" "jobs" {
  name         = "${var.name_prefix}-jobs"
  billing_mode = "PAY_PER_REQUEST"

  # Primary key (composite)
  hash_key  = "user_id"
  range_key = "job_id"

  # Table attributes
  attribute {
    name = "user_id"
    type = "S"  # String
  }

  attribute {
    name = "job_id"
    type = "S"  # String
  }

  attribute {
    name = "status"
    type = "S"  # String
  }

  # Global Secondary Index for status queries
  global_secondary_index {
    name            = "status-index"
    hash_key        = "status"
    projection_type = "ALL"
  }

  # TTL configuration
  ttl {
    attribute_name = "expires_at"
    enabled        = true
  }

  # Add tags for identification
  tags = {
    Name        = "${var.name_prefix}-jobs"
    Environment = var.environment
    Module      = "dynamodb"
  }
}