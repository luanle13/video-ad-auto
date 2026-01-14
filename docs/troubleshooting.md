# Troubleshooting Guide - AI Video Automation System

This document provides solutions for common issues and debugging techniques for the AI Video Platform.

---

## Quick Diagnostics

### System Health Check

```bash
# Check API health
curl https://api.your-domain.com/health

# Check Lambda status
aws lambda get-function --function-name ai-video-api --region ap-southeast-1

# Check DynamoDB tables
aws dynamodb describe-table --table-name ai-video-jobs --region ap-southeast-1

# Check Step Functions
aws stepfunctions describe-state-machine \
  --state-machine-arn arn:aws:states:ap-southeast-1:ACCOUNT:stateMachine:video-pipeline \
  --region ap-southeast-1
```

---

## Common Issues and Solutions

### Authentication Issues

#### Issue: "Invalid token" error

**Symptoms:**
- API returns 401 Unauthorized
- Token appears valid but is rejected

**Solutions:**

1. **Check token expiration:**
   ```python
   import jwt
   import base64
   
   # Decode without verification to check expiry
   token = "eyJ..."
   decoded = jwt.decode(token, options={"verify_signature": False})
   print(f"Expires: {decoded['exp']}")
   ```

2. **Verify Cognito configuration:**
   ```bash
   aws cognito-idp describe-user-pool \
     --user-pool-id ap-southeast-1_AbC123 \
     --region ap-southeast-1
   ```

3. **Refresh the token:**
   ```bash
   curl -X POST https://api.your-domain.com/auth/refresh \
     -H "Content-Type: application/json" \
     -d '{"refresh_token": "..."}'
   ```

#### Issue: User registration fails

**Symptoms:**
- "User already exists" error
- Cognito rejects password

**Solutions:**

1. **Password requirements:**
   - Minimum 8 characters
   - At least one uppercase letter
   - At least one lowercase letter
   - At least one number
   - At least one special character

2. **Check if user exists:**
   ```bash
   aws cognito-idp admin-get-user \
     --user-pool-id ap-southeast-1_AbC123 \
     --username user@example.com \
     --region ap-southeast-1
   ```

---

### Job Processing Issues

#### Issue: Job stuck in PENDING status

**Symptoms:**
- Job created but never starts processing
- No Step Functions execution visible

**Solutions:**

1. **Check Step Functions execution:**
   ```bash
   aws stepfunctions list-executions \
     --state-machine-arn arn:aws:states:ap-southeast-1:ACCOUNT:stateMachine:video-pipeline \
     --status-filter RUNNING \
     --region ap-southeast-1
   ```

2. **Check Lambda permissions:**
   ```bash
   aws lambda get-policy --function-name ai-video-api --region ap-southeast-1
   ```

3. **Verify state machine ARN in environment:**
   ```bash
   aws lambda get-function-configuration \
     --function-name ai-video-api \
     --region ap-southeast-1 \
     --query 'Environment.Variables'
   ```

#### Issue: Job fails with "Script generation failed"

**Symptoms:**
- Job status: FAILED
- Error message mentions OpenAI

**Solutions:**

1. **Check OpenAI API key:**
   ```bash
   aws secretsmanager get-secret-value \
     --secret-id ai-video/openai-api-key \
     --region ap-southeast-1
   ```

2. **Verify OpenAI quota:**
   - Check https://platform.openai.com/usage
   - Ensure billing is active

3. **Review agent Lambda logs:**
   ```bash
   aws logs filter-log-events \
     --log-group-name /aws/lambda/ai-video-agent \
     --filter-pattern "ERROR" \
     --start-time $(date -u -d '1 hour ago' +%s)000 \
     --region ap-southeast-1
   ```

#### Issue: TTS generation fails

**Symptoms:**
- Job fails at audio generation step
- Error mentions ElevenLabs

**Solutions:**

1. **Check ElevenLabs quota:**
   - Log into ElevenLabs dashboard
   - Verify character quota remaining

2. **Verify API key:**
   ```bash
   curl -H "xi-api-key: YOUR_KEY" \
     https://api.elevenlabs.io/v1/user
   ```

3. **Check TTS Lambda logs:**
   ```bash
   aws logs tail /aws/lambda/ai-video-tts --follow --region ap-southeast-1
   ```

#### Issue: Video generation fails

**Symptoms:**
- Job fails at video generation step
- Error mentions Kling AI

**Solutions:**

1. **Check Kling AI status:**
   - Verify API endpoint accessibility
   - Check for service announcements

2. **Review video Lambda logs:**
   ```bash
   aws logs filter-log-events \
     --log-group-name /aws/lambda/ai-video-video \
     --filter-pattern "ERROR" \
     --start-time $(date -u -d '1 hour ago' +%s)000 \
     --region ap-southeast-1
   ```

---

### Performance Issues

#### Issue: High API latency

**Symptoms:**
- API responses take >5 seconds
- Timeouts on frontend

**Solutions:**

1. **Check Lambda cold starts:**
   ```bash
   aws cloudwatch get-metric-statistics \
     --namespace AWS/Lambda \
     --metric-name Duration \
     --dimensions Name=FunctionName,Value=ai-video-api \
     --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ) \
     --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
     --period 60 \
     --statistics Maximum \
     --region ap-southeast-1
   ```

2. **Check DynamoDB throttling:**
   ```bash
   aws cloudwatch get-metric-statistics \
     --namespace AWS/DynamoDB \
     --metric-name ThrottledRequests \
     --dimensions Name=TableName,Value=ai-video-jobs \
     --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ) \
     --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
     --period 300 \
     --statistics Sum \
     --region ap-southeast-1
   ```

3. **Consider Provisioned Concurrency:**
   ```bash
   aws lambda put-provisioned-concurrency-config \
     --function-name ai-video-api \
     --qualifier prod \
     --provisioned-concurrent-executions 5 \
     --region ap-southeast-1
   ```

#### Issue: Lambda timeout

**Symptoms:**
- Lambda functions timing out
- "Task timed out" errors in CloudWatch

**Solutions:**

1. **Increase timeout (up to 15 minutes):**
   ```bash
   aws lambda update-function-configuration \
     --function-name ai-video-agent \
     --timeout 300 \
     --region ap-southeast-1
   ```

2. **Increase memory (more CPU):**
   ```bash
   aws lambda update-function-configuration \
     --function-name ai-video-agent \
     --memory-size 2048 \
     --region ap-southeast-1
   ```

---

### Infrastructure Issues

#### Issue: Terraform apply fails

**Symptoms:**
- Resource creation errors
- State lock issues

**Solutions:**

1. **State lock stuck:**
   ```bash
   terraform force-unlock LOCK_ID
   ```

2. **Resource already exists:**
   ```bash
   terraform import aws_lambda_function.api ai-video-api
   ```

3. **Permission denied:**
   - Verify IAM permissions
   - Check AWS credentials: `aws sts get-caller-identity`

#### Issue: S3 access denied

**Symptoms:**
- Cannot upload images
- Cannot download videos

**Solutions:**

1. **Check bucket policy:**
   ```bash
   aws s3api get-bucket-policy --bucket ai-video-images-prod --region ap-southeast-1
   ```

2. **Check CORS configuration:**
   ```bash
   aws s3api get-bucket-cors --bucket ai-video-images-prod --region ap-southeast-1
   ```

3. **Verify presigned URL:**
   ```python
   import boto3
   s3 = boto3.client('s3')
   url = s3.generate_presigned_url('put_object',
       Params={'Bucket': 'ai-video-images-prod', 'Key': 'test.jpg'},
       ExpiresIn=3600)
   print(url)
   ```

---

## Log Locations

### AWS CloudWatch Logs

| Component | Log Group |
|-----------|-----------|
| API Lambda | `/aws/lambda/ai-video-api` |
| Agent Lambda | `/aws/lambda/ai-video-agent` |
| TTS Lambda | `/aws/lambda/ai-video-tts` |
| Video Lambda | `/aws/lambda/ai-video-video` |
| API Gateway | `/aws/api-gateway/ai-video-api` |
| Step Functions | `/aws/states/video-pipeline` |

### Viewing Logs

```bash
# Tail logs in real-time
aws logs tail /aws/lambda/ai-video-api --follow --region ap-southeast-1

# Search for errors
aws logs filter-log-events \
  --log-group-name /aws/lambda/ai-video-api \
  --filter-pattern "ERROR" \
  --start-time $(date -u -d '1 hour ago' +%s)000 \
  --region ap-southeast-1

# Search for specific job
aws logs filter-log-events \
  --log-group-name /aws/lambda/ai-video-api \
  --filter-pattern "job-abc123" \
  --region ap-southeast-1
```

---

## Debugging Tips

### Enable Debug Logging

Set environment variable:
```bash
aws lambda update-function-configuration \
  --function-name ai-video-api \
  --environment "Variables={DEBUG=true,...}" \
  --region ap-southeast-1
```

### X-Ray Tracing

View traces in AWS Console:
1. Go to CloudWatch → X-Ray traces
2. Filter by service: `ai-video-api`
3. View trace timeline and segments

### Local Development

```bash
# Run API locally
cd backend
source .venv/bin/activate
ENVIRONMENT=dev DEBUG=true uvicorn src.api.main:app --reload

# Run frontend locally
cd frontend
npm run dev
```

### Testing External APIs

```bash
# Test OpenAI
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"

# Test ElevenLabs
curl https://api.elevenlabs.io/v1/user \
  -H "xi-api-key: $ELEVENLABS_API_KEY"

# Test Kling AI
curl https://api.klingai.com/v1/health \
  -H "Authorization: Bearer $KLING_API_KEY"
```

---

## Escalation Path

If issues persist after trying the above solutions:

1. **Check CloudWatch Alarms** - Review any triggered alarms
2. **Review Recent Deployments** - Check GitHub Actions for recent changes
3. **Check AWS Status** - https://status.aws.amazon.com
4. **Review Incident Runbook** - `/docs/runbook/incident-response.md`

---

## Related Documents

- [Architecture Overview](/docs/architecture.md)
- [Deployment Guide](/docs/deployment.md)
- [Incident Response](/docs/runbook/incident-response.md)
- [Secrets Rotation](/docs/runbook/secrets-rotation.md)
