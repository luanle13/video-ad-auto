# IAM role for Step Functions execution
resource "aws_iam_role" "stepfunctions_execution" {
  name = "${var.project_name}-stepfunctions-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "states.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = var.tags
}

# IAM policy for Step Functions to invoke Lambdas
resource "aws_iam_role_policy" "invoke_lambdas" {
  name = "invoke-lambdas"
  role = aws_iam_role.stepfunctions_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "lambda:InvokeFunction"
        ]
        Resource = [
          var.agent_lambda_arn,
          var.tts_lambda_arn,
          var.video_lambda_arn
        ]
      }
    ]
  })
}

# IAM policy for Step Functions to access DynamoDB
resource "aws_iam_role_policy" "dynamodb_access" {
  name = "dynamodb-access"
  role = aws_iam_role.stepfunctions_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem"
        ]
        Resource = var.dynamodb_jobs_table_arn
      }
    ]
  })
}

# IAM policy for Step Functions to access S3
resource "aws_iam_role_policy" "s3_access" {
  name = "s3-access"
  role = aws_iam_role.stepfunctions_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject"
        ]
        Resource = "${var.s3_videos_bucket_arn}/*"
      }
    ]
  })
}

# CloudWatch Logs for Step Functions
resource "aws_cloudwatch_log_group" "stepfunctions" {
  name              = "/aws/stepfunctions/${var.project_name}-video-pipeline-${var.environment}"
  retention_in_days = 30

  tags = var.tags
}

# IAM policy for Step Functions to write CloudWatch Logs
resource "aws_iam_role_policy" "cloudwatch_logs" {
  name = "cloudwatch-logs"
  role = aws_iam_role.stepfunctions_execution.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogDelivery",
          "logs:GetLogDelivery",
          "logs:UpdateLogDelivery",
          "logs:DeleteLogDelivery",
          "logs:ListLogDeliveries",
          "logs:PutResourcePolicy",
          "logs:DescribeResourcePolicies",
          "logs:DescribeLogGroups"
        ]
        Resource = "*"
      }
    ]
  })
}

# Step Functions State Machine
resource "aws_sfn_state_machine" "video_pipeline" {
  name     = "${var.project_name}-video-pipeline-${var.environment}"
  role_arn = aws_iam_role.stepfunctions_execution.arn

  logging_configuration {
    log_destination        = "${aws_cloudwatch_log_group.stepfunctions.arn}:*"
    include_execution_data = true
    level                  = "ALL"
  }

  definition = jsonencode({
    Comment = "AI Video Generation Pipeline - Orchestrates agents, TTS, and video generation"
    StartAt = "ValidateInput"
    TimeoutSeconds = 900  # 15 minutes

    States = {
      # Step 1: Validate Input
      ValidateInput = {
        Type = "Pass"
        Comment = "Validate input and initialize job context"
        Parameters = {
          "user_id.$" = "$.user_id"
          "job_id.$" = "$.job_id"
          "product.$" = "$.product"
          "adjustments.$" = "$.adjustments"
          "context" = {}
        }
        Next = "UpdateStatusProcessing"
      }

      # Update job status to PROCESSING
      UpdateStatusProcessing = {
        Type = "Task"
        Resource = "arn:aws:states:::dynamodb:updateItem"
        Parameters = {
          TableName = var.dynamodb_jobs_table_name
          Key = {
            user_id = {
              "S.$" = "$.user_id"
            }
            job_id = {
              "S.$" = "$.job_id"
            }
          }
          UpdateExpression = "SET #status = :status, updated_at = :now"
          ExpressionAttributeNames = {
            "#status" = "status"
          }
          ExpressionAttributeValues = {
            ":status" = {
              S = "PROCESSING"
            }
            ":now" = {
              "S.$" = "$$.State.EnteredTime"
            }
          }
        }
        ResultPath = null
        Next = "ProductAnalyzer"
        Catch = [
          {
            ErrorEquals = ["States.ALL"]
            ResultPath = "$.error"
            Next = "HandleError"
          }
        ]
      }

      # Step 2: Product Analyzer Agent
      ProductAnalyzer = {
        Type = "Task"
        Resource = "arn:aws:states:::lambda:invoke"
        Parameters = {
          FunctionName = var.agent_lambda_arn
          Payload = {
            "task" = "analyze"
            "user_id.$" = "$.user_id"
            "job_id.$" = "$.job_id"
            "product.$" = "$.product"
            "context.$" = "$.context"
            "adjustments.$" = "$.adjustments"
          }
        }
        ResultSelector = {
          "output.$" = "$.Payload.output"
        }
        ResultPath = "$.context.analyze"
        TimeoutSeconds = 180
        Retry = [
          {
            ErrorEquals = ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException"]
            IntervalSeconds = 2
            MaxAttempts = 2
            BackoffRate = 2.0
          }
        ]
        Catch = [
          {
            ErrorEquals = ["States.ALL"]
            ResultPath = "$.error"
            Next = "HandleError"
          }
        ]
        Next = "ScriptGenerator"
      }

      # Step 3: Script Generator Agent
      ScriptGenerator = {
        Type = "Task"
        Resource = "arn:aws:states:::lambda:invoke"
        Parameters = {
          FunctionName = var.agent_lambda_arn
          Payload = {
            "task" = "generate"
            "user_id.$" = "$.user_id"
            "job_id.$" = "$.job_id"
            "product.$" = "$.product"
            "context.$" = "$.context"
            "adjustments.$" = "$.adjustments"
          }
        }
        ResultSelector = {
          "output.$" = "$.Payload.output"
        }
        ResultPath = "$.context.generate"
        TimeoutSeconds = 180
        Retry = [
          {
            ErrorEquals = ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException"]
            IntervalSeconds = 2
            MaxAttempts = 2
            BackoffRate = 2.0
          }
        ]
        Catch = [
          {
            ErrorEquals = ["States.ALL"]
            ResultPath = "$.error"
            Next = "HandleError"
          }
        ]
        Next = "ScriptOptimizer"
      }

      # Step 4: Script Optimizer Agent
      ScriptOptimizer = {
        Type = "Task"
        Resource = "arn:aws:states:::lambda:invoke"
        Parameters = {
          FunctionName = var.agent_lambda_arn
          Payload = {
            "task" = "optimize"
            "user_id.$" = "$.user_id"
            "job_id.$" = "$.job_id"
            "product.$" = "$.product"
            "context.$" = "$.context"
            "adjustments.$" = "$.adjustments"
          }
        }
        ResultSelector = {
          "output.$" = "$.Payload.output"
        }
        ResultPath = "$.context.optimize"
        TimeoutSeconds = 180
        Retry = [
          {
            ErrorEquals = ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException"]
            IntervalSeconds = 2
            MaxAttempts = 2
            BackoffRate = 2.0
          }
        ]
        Catch = [
          {
            ErrorEquals = ["States.ALL"]
            ResultPath = "$.error"
            Next = "HandleError"
          }
        ]
        Next = "ScriptReviewer"
      }

      # Step 5: Script Reviewer Agent
      ScriptReviewer = {
        Type = "Task"
        Resource = "arn:aws:states:::lambda:invoke"
        Parameters = {
          FunctionName = var.agent_lambda_arn
          Payload = {
            "task" = "review"
            "user_id.$" = "$.user_id"
            "job_id.$" = "$.job_id"
            "product.$" = "$.product"
            "context.$" = "$.context"
            "adjustments.$" = "$.adjustments"
          }
        }
        ResultSelector = {
          "output.$" = "$.Payload.output"
        }
        ResultPath = "$.context.review"
        TimeoutSeconds = 180
        Retry = [
          {
            ErrorEquals = ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException"]
            IntervalSeconds = 2
            MaxAttempts = 2
            BackoffRate = 2.0
          }
        ]
        Catch = [
          {
            ErrorEquals = ["States.ALL"]
            ResultPath = "$.error"
            Next = "HandleError"
          }
        ]
        Next = "CheckReviewApproval"
      }

      # Check if script was approved by reviewer
      CheckReviewApproval = {
        Type = "Choice"
        Choices = [
          {
            Variable = "$.context.review.output.approved"
            BooleanEquals = true
            Next = "TTSGeneration"
          }
        ]
        Default = "HandleReviewRejection"
      }

      # Handle script rejection
      HandleReviewRejection = {
        Type = "Task"
        Resource = "arn:aws:states:::dynamodb:updateItem"
        Parameters = {
          TableName = var.dynamodb_jobs_table_name
          Key = {
            user_id = {
              "S.$" = "$.user_id"
            }
            job_id = {
              "S.$" = "$.job_id"
            }
          }
          UpdateExpression = "SET #status = :status, updated_at = :now, error_message = :error"
          ExpressionAttributeNames = {
            "#status" = "status"
          }
          ExpressionAttributeValues = {
            ":status" = {
              S = "FAILED"
            }
            ":now" = {
              "S.$" = "$$.State.EnteredTime"
            }
            ":error" = {
              "S.$" = "States.Format('Script review failed: {}', $.context.review.output.review_summary)"
            }
          }
        }
        End = true
      }

      # Step 6: TTS Generation
      TTSGeneration = {
        Type = "Task"
        Resource = "arn:aws:states:::lambda:invoke"
        Parameters = {
          FunctionName = var.tts_lambda_arn
          Payload = {
            "user_id.$" = "$.user_id"
            "job_id.$" = "$.job_id"
            "voiceover_text.$" = "$.context.review.output.final_voiceover"
            "voice_settings.$" = "$.adjustments.voice_settings"
          }
        }
        ResultSelector = {
          "audio_key.$" = "$.Payload.audio_key"
          "duration_seconds.$" = "$.Payload.duration_seconds"
        }
        ResultPath = "$.context.tts"
        TimeoutSeconds = 120
        Retry = [
          {
            ErrorEquals = ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException"]
            IntervalSeconds = 2
            MaxAttempts = 2
            BackoffRate = 2.0
          }
        ]
        Catch = [
          {
            ErrorEquals = ["States.ALL"]
            ResultPath = "$.error"
            Next = "HandleError"
          }
        ]
        Next = "VideoGeneration"
      }

      # Step 7: Video Generation
      VideoGeneration = {
        Type = "Task"
        Resource = "arn:aws:states:::lambda:invoke"
        Parameters = {
          FunctionName = var.video_lambda_arn
          Payload = {
            "user_id.$" = "$.user_id"
            "job_id.$" = "$.job_id"
            "product_images.$" = "$.product.image_keys"
            "scenes.$" = "$.context.review.output.final_scenes"
            "audio_key.$" = "$.context.tts.audio_key"
            "duration_seconds.$" = "$.context.tts.duration_seconds"
            "text_overlays.$" = "$.context.generate.output.text_overlays"
          }
        }
        ResultSelector = {
          "video_key.$" = "$.Payload.video_key"
          "task_id.$" = "$.Payload.task_id"
        }
        ResultPath = "$.context.video"
        TimeoutSeconds = 600
        Retry = [
          {
            ErrorEquals = ["Lambda.ServiceException", "Lambda.AWSLambdaException", "Lambda.SdkClientException"]
            IntervalSeconds = 5
            MaxAttempts = 3
            BackoffRate = 2.0
          }
        ]
        Catch = [
          {
            ErrorEquals = ["States.ALL"]
            ResultPath = "$.error"
            Next = "HandleError"
          }
        ]
        Next = "UpdateJobComplete"
      }

      # Step 8: Update job to COMPLETE
      UpdateJobComplete = {
        Type = "Task"
        Resource = "arn:aws:states:::dynamodb:updateItem"
        Parameters = {
          TableName = var.dynamodb_jobs_table_name
          Key = {
            user_id = {
              "S.$" = "$.user_id"
            }
            job_id = {
              "S.$" = "$.job_id"
            }
          }
          UpdateExpression = "SET #status = :status, updated_at = :now, video_key = :video, audio_key = :audio"
          ExpressionAttributeNames = {
            "#status" = "status"
          }
          ExpressionAttributeValues = {
            ":status" = {
              S = "COMPLETE"
            }
            ":now" = {
              "S.$" = "$$.State.EnteredTime"
            }
            ":video" = {
              "S.$" = "$.context.video.video_key"
            }
            ":audio" = {
              "S.$" = "$.context.tts.audio_key"
            }
          }
        }
        ResultPath = null
        Next = "Success"
      }

      # Success state
      Success = {
        Type = "Succeed"
      }

      # Error handling
      HandleError = {
        Type = "Task"
        Resource = "arn:aws:states:::dynamodb:updateItem"
        Parameters = {
          TableName = var.dynamodb_jobs_table_name
          Key = {
            user_id = {
              "S.$" = "$.user_id"
            }
            job_id = {
              "S.$" = "$.job_id"
            }
          }
          UpdateExpression = "SET #status = :status, updated_at = :now, error_message = :error"
          ExpressionAttributeNames = {
            "#status" = "status"
          }
          ExpressionAttributeValues = {
            ":status" = {
              S = "FAILED"
            }
            ":now" = {
              "S.$" = "$$.State.EnteredTime"
            }
            ":error" = {
              "S.$" = "States.Format('Pipeline failed: {} - {}', $.error.Error, $.error.Cause)"
            }
          }
        }
        ResultPath = null
        Next = "Fail"
      }

      # Fail state
      Fail = {
        Type = "Fail"
        Error = "PipelineExecutionFailed"
        Cause = "The video generation pipeline encountered an error"
      }
    }
  })

  tags = var.tags
}
