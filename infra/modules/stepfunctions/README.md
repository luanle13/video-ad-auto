# Step Functions Module

This Terraform module creates an AWS Step Functions state machine that orchestrates the AI video generation pipeline.

## Architecture

The state machine implements a sequential pipeline with error handling:

```
ValidateInput
    ↓
UpdateStatusProcessing
    ↓
ProductAnalyzer (Agent Lambda)
    ↓
ScriptGenerator (Agent Lambda)
    ↓
ScriptOptimizer (Agent Lambda)
    ↓
ScriptReviewer (Agent Lambda)
    ↓
CheckReviewApproval
    ↓
TTSGeneration (TTS Lambda)
    ↓
VideoGeneration (Video Lambda)
    ↓
UpdateJobComplete
    ↓
Success
```

All steps have error handling that catches failures and updates the job status to FAILED in DynamoDB.

## Features

- **Timeout**: 15 minutes total execution time
- **Retry Logic**: 2 retries with exponential backoff on transient Lambda errors
- **Error Handling**: All errors caught and stored in DynamoDB with error messages
- **Logging**: Full execution logging to CloudWatch Logs
- **Status Updates**: Job status updated at key stages (PROCESSING → COMPLETE/FAILED)
- **Review Gate**: Script must pass review before proceeding to TTS/video generation

## Resources Created

- Step Functions state machine
- IAM role for state machine execution
- IAM policies for Lambda invocation, DynamoDB access, S3 access, CloudWatch Logs
- CloudWatch Log Group for execution logs

## Inputs

| Variable | Description | Type | Required |
|----------|-------------|------|----------|
| project_name | Project name for resource naming | string | Yes |
| environment | Environment (dev/prod) | string | Yes |
| agent_lambda_arn | ARN of agent worker Lambda | string | Yes |
| tts_lambda_arn | ARN of TTS worker Lambda | string | Yes |
| video_lambda_arn | ARN of video worker Lambda | string | Yes |
| dynamodb_jobs_table_name | Name of DynamoDB jobs table | string | Yes |
| dynamodb_jobs_table_arn | ARN of DynamoDB jobs table | string | Yes |
| s3_videos_bucket_arn | ARN of S3 videos bucket | string | Yes |
| tags | Tags to apply to all resources | map(string) | No |

## Outputs

| Output | Description |
|--------|-------------|
| state_machine_arn | ARN of the Step Functions state machine |
| state_machine_name | Name of the Step Functions state machine |
| execution_role_arn | ARN of the execution IAM role |

## Usage

```hcl
module "stepfunctions" {
  source = "./modules/stepfunctions"

  project_name = "ai-video"
  environment  = "prod"

  agent_lambda_arn  = module.lambda_agent.function_arn
  tts_lambda_arn    = module.lambda_tts.function_arn
  video_lambda_arn  = module.lambda_video.function_arn

  dynamodb_jobs_table_name = module.dynamodb.jobs_table_name
  dynamodb_jobs_table_arn  = module.dynamodb.jobs_table_arn
  s3_videos_bucket_arn     = module.s3.videos_bucket_arn

  tags = {
    Project     = "AI Video Automation"
    Environment = "prod"
    ManagedBy   = "Terraform"
  }
}
```

## Execution Input Format

The state machine expects this input structure:

```json
{
  "user_id": "usr_123",
  "job_id": "job_456",
  "product": {
    "id": "prod_789",
    "title": "Wireless Earbuds Pro",
    "description": "High-quality wireless earbuds with ANC",
    "price": "799,000 VND",
    "image_keys": ["images/prod_789/img1.jpg", "images/prod_789/img2.jpg"]
  },
  "adjustments": {
    "tone": "energetic",
    "target_duration": 45,
    "primary_platform": "tiktok",
    "voice_settings": {
      "voice_id": "EXAVITQu4vr4xnSDxMaL",
      "stability": 0.5,
      "similarity_boost": 0.75
    }
  }
}
```

## IAM Permissions

The execution role has least-privilege permissions:

- **Lambda**: Invoke only specified functions (agent, TTS, video)
- **DynamoDB**: GetItem, PutItem, UpdateItem on jobs table only
- **S3**: GetObject, PutObject on videos bucket only
- **CloudWatch Logs**: Write execution logs

## Error Handling

All Lambda invocations have:
- 2 retry attempts with exponential backoff (2x)
- Catch block that routes to HandleError state
- Error details stored in job.error_message in DynamoDB

Errors handled:
- Lambda service errors (throttling, capacity)
- Lambda function errors (runtime errors, timeouts)
- DynamoDB errors (throttling, validation)
- Script review rejection (compliance failures)

## Monitoring

CloudWatch Logs include:
- Full execution history with timestamps
- Input/output data for each step
- Error details and stack traces
- 30-day retention period

## Cost Optimization

- On-demand DynamoDB to avoid over-provisioning
- 30-day log retention to control storage costs
- Retry logic prevents unnecessary re-executions
- 15-minute timeout prevents runaway executions
