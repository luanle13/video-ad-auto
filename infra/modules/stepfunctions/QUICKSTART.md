# Step Functions Quick Start Guide

## 🚀 Quick Deploy

### 1. Add Module to Main Terraform

```hcl
# main.tf
module "stepfunctions" {
  source = "./modules/stepfunctions"

  project_name = var.project_name
  environment  = var.environment

  # Lambda ARNs (from Lambda modules)
  agent_lambda_arn = module.lambda_agent.function_arn
  tts_lambda_arn   = module.lambda_tts.function_arn
  video_lambda_arn = module.lambda_video.function_arn

  # DynamoDB table
  dynamodb_jobs_table_name = aws_dynamodb_table.jobs.name
  dynamodb_jobs_table_arn  = aws_dynamodb_table.jobs.arn

  # S3 bucket
  s3_videos_bucket_arn = aws_s3_bucket.videos.arn

  tags = local.common_tags
}
```

### 2. Configure Environment Variable

```bash
# .env or environment
export STEPFUNCTIONS_STATE_MACHINE_ARN="${module.stepfunctions.state_machine_arn}"
```

### 3. Deploy

```bash
cd infra
terraform init
terraform plan
terraform apply
```

## 📝 Using in Python Code

### Start an Execution

```python
from src.shared import get_stepfunctions_client

sfn = get_stepfunctions_client()

execution_arn = sfn.start_execution(
    user_id="usr_123",
    job_id="job_456",
    product={
        "id": "prod_789",
        "title": "Wireless Earbuds Pro",
        "description": "High-quality earbuds",
        "price": "799,000 VND",
        "image_keys": ["images/prod_789/img1.jpg"]
    },
    adjustments={
        "tone": "energetic",
        "target_duration": 45,
        "primary_platform": "tiktok"
    }
)

print(f"Started execution: {execution_arn}")
```

### Check Status

```python
status = sfn.get_execution_status(execution_arn)

print(f"Status: {status['status']}")
print(f"Started: {status['start_date']}")

if status['status'] == 'SUCCEEDED':
    print(f"Output: {status['output']}")
elif status['status'] == 'FAILED':
    print(f"Error: {status['error']}")
```

### List Recent Executions

```python
# All executions
executions = sfn.list_executions(max_results=10)

# Only running
running = sfn.list_executions(status="RUNNING")

# Only failed
failed = sfn.list_executions(status="FAILED")

for exec in executions:
    print(f"{exec['name']}: {exec['status']}")
```

### Stop an Execution

```python
sfn.stop_execution(
    execution_arn=execution_arn,
    error="User cancelled",
    cause="User requested cancellation from UI"
)
```

## 🔧 Integration with FastAPI

### Jobs Route Example

```python
from fastapi import APIRouter, Depends
from src.shared import get_db, get_stepfunctions_client
from src.api.dependencies.auth import get_current_user

router = APIRouter()

@router.post("/jobs")
async def create_job(
    request: CreateJobRequest,
    user = Depends(get_current_user),
    db = Depends(get_db),
    sfn = Depends(get_stepfunctions_client),
):
    # 1. Get product
    product = db.get_product(user.user_id, request.product_id)

    # 2. Create job record
    job = db.create_job(
        user_id=user.user_id,
        product_id=request.product_id,
        adjustments=request.adjustments,
    )

    # 3. Start Step Functions execution
    execution_arn = sfn.start_execution(
        user_id=user.user_id,
        job_id=job["job_id"],
        product=product,
        adjustments=request.adjustments or {},
    )

    # 4. Store execution ARN
    db.update_job_step_output(
        user_id=user.user_id,
        job_id=job["job_id"],
        step_name="execution",
        output={"execution_arn": execution_arn}
    )

    return {"job_id": job["job_id"], "status": "PROCESSING"}


@router.get("/jobs/{job_id}")
async def get_job(
    job_id: str,
    user = Depends(get_current_user),
    db = Depends(get_db),
    sfn = Depends(get_stepfunctions_client),
):
    # Get job from DB
    job = db.get_job(user.user_id, job_id)

    # If execution exists, get current status
    execution_arn = job.get("step_outputs", {}).get("execution", {}).get("execution_arn")
    if execution_arn:
        try:
            status = sfn.get_execution_status(execution_arn)
            job["execution_status"] = status["status"]

            if status["status"] == "FAILED":
                job["execution_error"] = status.get("error")
        except Exception:
            pass  # Execution may have expired from history

    return job
```

## 🧪 Testing

### Run Unit Tests

```bash
cd backend
python3 -m pytest tests/unit/shared/test_stepfunctions.py -v
```

### Test Coverage

```bash
python3 -m pytest tests/unit/shared/test_stepfunctions.py --cov=src/shared/stepfunctions --cov-report=html
```

### Manual Testing with AWS CLI

```bash
# Start execution
aws stepfunctions start-execution \
  --state-machine-arn "arn:aws:states:ap-southeast-1:123456789012:stateMachine:ai-video-pipeline-dev" \
  --name "test-$(date +%s)" \
  --input file://test-input.json

# Get status
aws stepfunctions describe-execution \
  --execution-arn "arn:aws:states:...:execution:..."

# List executions
aws stepfunctions list-executions \
  --state-machine-arn "arn:aws:states:..." \
  --status-filter RUNNING
```

## 📊 Monitoring

### View Logs

```bash
# CloudWatch Logs Insights query
aws logs start-query \
  --log-group-name "/aws/stepfunctions/ai-video-pipeline-dev" \
  --start-time $(date -u -d '1 hour ago' +%s) \
  --end-time $(date -u +%s) \
  --query-string "fields @timestamp, @message | sort @timestamp desc"
```

### Metrics Dashboard

Key metrics to monitor:
- `ExecutionsStarted` - Total executions started
- `ExecutionsSucceeded` - Successful completions
- `ExecutionsFailed` - Failed executions (alert on this!)
- `ExecutionTime` - Average execution duration
- `ExecutionThrottled` - Throttled starts (increase concurrency if needed)

### Set Up Alarms

```hcl
resource "aws_cloudwatch_metric_alarm" "high_failure_rate" {
  alarm_name          = "${var.project_name}-stepfunctions-high-failures-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "ExecutionsFailed"
  namespace           = "AWS/States"
  period              = 300  # 5 minutes
  statistic           = "Sum"
  threshold           = 5
  alarm_description   = "Alert when >5 Step Functions executions fail in 5 minutes"

  dimensions = {
    StateMachineArn = module.stepfunctions.state_machine_arn
  }

  alarm_actions = [aws_sns_topic.alerts.arn]
}
```

## 🐛 Debugging

### Common Issues

#### 1. Execution Not Starting

**Symptom**: `ValidationException: State machine ARN not configured`

**Fix**:
```python
# Check config
from src.shared.config import get_settings
settings = get_settings()
print(settings.stepfunctions_state_machine_arn)  # Should not be empty

# Set environment variable
export STEPFUNCTIONS_STATE_MACHINE_ARN="arn:aws:states:..."
```

#### 2. Lambda Not Invoked

**Symptom**: `States.TaskFailed: Lambda function failed`

**Debug**:
1. Check CloudWatch Logs for state machine
2. Look for error in Lambda CloudWatch Logs
3. Verify Lambda IAM role has permissions
4. Check Lambda function exists and is deployed

#### 3. DynamoDB Update Failed

**Symptom**: `ResourceNotFoundException: Requested resource not found`

**Debug**:
1. Verify table name in Terraform matches Settings
2. Check IAM role has DynamoDB permissions
3. Ensure partition key (user_id) and sort key (job_id) are correct

#### 4. Script Review Rejection

**Symptom**: Execution ends at `HandleReviewRejection`

**Expected behavior**: This is not an error! The script failed compliance review.

**Check**:
```python
job = db.get_job(user_id, job_id)
review_output = job["step_outputs"]["review"]
print(review_output["review_summary"])
print(review_output["critical_issues"])
```

### Viewing Execution History

AWS Console:
1. Go to Step Functions → State machines
2. Click on `ai-video-pipeline-{env}`
3. Click "Executions" tab
4. Click on specific execution to see visual workflow

AWS CLI:
```bash
aws stepfunctions get-execution-history \
  --execution-arn "arn:aws:states:..." \
  --max-results 100
```

## 💡 Tips & Best Practices

### 1. Use Unique Job IDs

Always use UUID or similar for job IDs to ensure unique execution names:

```python
from uuid import uuid4

job_id = str(uuid4())  # e.g., "550e8400-e29b-41d4-a716-446655440000"
```

### 2. Handle Execution Already Exists

The client automatically handles this:

```python
# First call
arn1 = sfn.start_execution(user_id, job_id, product)

# Second call with same job_id - returns existing ARN
arn2 = sfn.start_execution(user_id, job_id, product)

assert arn1 == arn2  # Same execution
```

### 3. Store Execution ARN in Job

Always store the execution ARN so you can check status later:

```python
db.update_job_step_output(
    user_id=user_id,
    job_id=job_id,
    step_name="execution",
    output={"execution_arn": execution_arn}
)
```

### 4. Poll Status Wisely

Don't poll too frequently - executions take minutes:

```python
import time

while True:
    status = sfn.get_execution_status(execution_arn)
    if status["status"] in ["SUCCEEDED", "FAILED", "ABORTED", "TIMED_OUT"]:
        break
    time.sleep(30)  # Poll every 30 seconds
```

### 5. Clean Up Old Executions

Step Functions keeps execution history for 90 days. For compliance:

```python
# List old executions
old_executions = sfn.list_executions(status="SUCCEEDED", max_results=1000)

# Clean up job records after verification
for exec in old_executions:
    # Archive or delete based on your retention policy
    pass
```

## 🔒 Security Checklist

- [ ] State machine ARN stored in environment variable, not code
- [ ] IAM roles follow least privilege (no wildcards)
- [ ] CloudWatch Logs encryption enabled
- [ ] DynamoDB table encryption at rest enabled
- [ ] S3 bucket encryption at rest enabled
- [ ] Input validation in Lambda functions (Pydantic models)
- [ ] Error messages sanitized before storing in DynamoDB
- [ ] API authentication required (Cognito JWT)
- [ ] Rate limiting on API endpoints
- [ ] Execution names don't contain sensitive data

## 📚 Additional Resources

- [AWS Step Functions Documentation](https://docs.aws.amazon.com/step-functions/)
- [Amazon States Language (ASL) Spec](https://states-language.net/spec.html)
- [Step Functions Best Practices](https://docs.aws.amazon.com/step-functions/latest/dg/sfn-best-practices.html)
- [Terraform AWS Provider - Step Functions](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/sfn_state_machine)

## 🆘 Support

Issues with the implementation? Check:
1. [README.md](README.md) - Detailed architecture and usage
2. [STEPFUNCTIONS_IMPLEMENTATION.md](/STEPFUNCTIONS_IMPLEMENTATION.md) - Complete implementation summary
3. Tests: `backend/tests/unit/shared/test_stepfunctions.py`
4. CloudWatch Logs: `/aws/stepfunctions/ai-video-pipeline-{env}`
