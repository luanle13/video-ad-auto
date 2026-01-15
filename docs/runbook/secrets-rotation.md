# Secrets Rotation Procedure

This document outlines the procedures for rotating secrets used by the AI Video Automation System.

## Overview

All secrets are stored in AWS Secrets Manager and accessed by Lambda functions at runtime. Regular rotation reduces the risk of compromised credentials and ensures compliance with security policies.

### Secrets Inventory

| Secret Name | Service | Rotation Frequency | Owner |
|-------------|---------|-------------------|-------|
| `openai-api-key` | OpenAI GPT API | 90 days | Platform Team |
| `elevenlabs-api-key` | ElevenLabs TTS API | 90 days | Platform Team |
| `kling-api-key` | Kling Video Generation API | 90 days | Platform Team |

---

## Scheduled Rotation

### Prerequisites

- AWS CLI configured with appropriate permissions
- Access to respective service dashboards
- Secrets Manager write permissions

### ElevenLabs API Key

1. **Generate new key in ElevenLabs dashboard**
   - Log in to [ElevenLabs](https://elevenlabs.io)
   - Navigate to Profile > API Keys
   - Click "Create API Key"
   - Copy the new key

2. **Update secret in Secrets Manager**
   ```bash
   aws secretsmanager update-secret \
     --secret-id elevenlabs-api-key \
     --secret-string '{"api_key": "NEW_KEY_HERE"}' \
     --region ap-southeast-1
   ```

3. **Test TTS generation**
   ```bash
   # Invoke the TTS Lambda with a test payload
   aws lambda invoke \
     --function-name video-platform-tts-lambda \
     --payload '{"text": "Test audio generation", "voice_id": "default"}' \
     --region ap-southeast-1 \
     response.json

   # Verify successful response
   cat response.json
   ```

4. **Revoke old key**
   - Return to ElevenLabs dashboard
   - Delete the old API key

---

### Kling API Key

1. **Generate new key in Kling console**
   - Log in to [Kling AI Console](https://klingai.com)
   - Navigate to API Settings
   - Generate a new API key
   - Copy the new key

2. **Update secret in Secrets Manager**
   ```bash
   aws secretsmanager update-secret \
     --secret-id kling-api-key \
     --secret-string '{"api_key": "NEW_KEY_HERE"}' \
     --region ap-southeast-1
   ```

3. **Test video generation**
   ```bash
   # Invoke the video Lambda with a test payload
   aws lambda invoke \
     --function-name video-platform-video-lambda \
     --payload '{"test": true, "action": "health_check"}' \
     --region ap-southeast-1 \
     response.json

   # Verify successful response
   cat response.json
   ```

4. **Revoke old key**
   - Return to Kling console
   - Delete the old API key

---

### OpenAI API Key

1. **Generate new key in OpenAI dashboard**
   - Log in to [OpenAI Platform](https://platform.openai.com)
   - Navigate to API Keys
   - Click "Create new secret key"
   - Name it with date suffix (e.g., `video-platform-2024-01`)
   - Copy the new key

2. **Update secret in Secrets Manager**
   ```bash
   aws secretsmanager update-secret \
     --secret-id openai-api-key \
     --secret-string '{"api_key": "NEW_KEY_HERE"}' \
     --region ap-southeast-1
   ```

3. **Verify CrewAI agents work**
   ```bash
   # Invoke the agent Lambda with a test payload
   aws lambda invoke \
     --function-name video-platform-agent-lambda \
     --payload '{"test": true}' \
     --region ap-southeast-1 \
     response.json

   # Check response for success
   cat response.json
   ```

4. **Revoke old key**
   - Return to OpenAI Platform
   - Delete the old API key

---

## Emergency Rotation

Use this procedure when a key is suspected or confirmed to be compromised.

### Immediate Actions (Within 15 Minutes)

1. **Revoke compromised key immediately**
   - Do NOT wait to create a new key first
   - Access the respective service console
   - Revoke/delete the compromised key
   - This will cause temporary service disruption

2. **Generate and deploy new key**
   ```bash
   # Update Secrets Manager with new key
   aws secretsmanager update-secret \
     --secret-id <SECRET_NAME> \
     --secret-string '{"api_key": "NEW_KEY_HERE"}' \
     --region ap-southeast-1
   ```

3. **Force Lambda to pick up new secret**
   ```bash
   # Update Lambda configuration to force cold start
   aws lambda update-function-configuration \
     --function-name <FUNCTION_NAME> \
     --environment "Variables={FORCE_REFRESH=$(date +%s)}" \
     --region ap-southeast-1
   ```

4. **Verify service restoration**
   - Run health checks on affected services
   - Monitor CloudWatch logs for errors
   - Confirm successful API calls

### Notification Contacts

| Role | Name | Contact | Escalation Level |
|------|------|---------|------------------|
| Primary On-Call | Platform Team | platform-oncall@company.com | L1 |
| Security Lead | Security Team | security@company.com | L2 |
| Engineering Manager | Engineering | eng-manager@company.com | L3 |

### Notification Template

```
SUBJECT: [SECURITY] Emergency Secret Rotation - <SERVICE_NAME>

SEVERITY: High
TIME DETECTED: <TIMESTAMP>
SECRET AFFECTED: <SECRET_NAME>

ACTIONS TAKEN:
1. Old key revoked at <TIME>
2. New key generated and deployed at <TIME>
3. Services verified operational at <TIME>

IMPACT:
- Service downtime: <DURATION>
- Affected components: <LIST>

ROOT CAUSE: <DESCRIPTION>

FOLLOW-UP ACTIONS:
- [ ] Review access logs for unauthorized usage
- [ ] Update incident report
- [ ] Schedule post-mortem if needed
```

### Verification Steps

After emergency rotation, complete these verification steps:

1. **Check CloudWatch Logs**
   ```bash
   aws logs filter-log-events \
     --log-group-name /aws/lambda/video-platform-agent-lambda \
     --start-time $(date -d '1 hour ago' +%s)000 \
     --filter-pattern "ERROR" \
     --region ap-southeast-1
   ```

2. **Run Integration Tests**
   ```bash
   # From project root
   cd backend
   pytest tests/integration/ -v --tb=short
   ```

3. **Monitor Metrics**
   - Check CloudWatch dashboard for error rates
   - Verify API response times are normal
   - Confirm no 401/403 errors in logs

4. **Review Audit Trail**
   ```bash
   # Check Secrets Manager access history
   aws secretsmanager describe-secret \
     --secret-id <SECRET_NAME> \
     --region ap-southeast-1

   # Review CloudTrail for secret access
   aws cloudtrail lookup-events \
     --lookup-attributes AttributeKey=ResourceName,AttributeValue=<SECRET_ARN> \
     --start-time $(date -d '24 hours ago' --iso-8601) \
     --region ap-southeast-1
   ```

---

## Post-Rotation Checklist

- [ ] New key generated and stored in Secrets Manager
- [ ] Lambda functions tested and operational
- [ ] Old key revoked in service console
- [ ] Rotation logged in security audit trail
- [ ] Team notified of completed rotation
- [ ] Next rotation date scheduled (90 days)

---

## Automation

For automated rotation, consider implementing AWS Secrets Manager automatic rotation:

```hcl
# Terraform example for automatic rotation
resource "aws_secretsmanager_secret_rotation" "example" {
  secret_id           = aws_secretsmanager_secret.api_key.id
  rotation_lambda_arn = aws_lambda_function.rotation.arn

  rotation_rules {
    automatically_after_days = 90
  }
}
```

**Note:** Automatic rotation requires custom Lambda rotation functions for each third-party API, as they don't support AWS-native rotation.

---

## Related Documents

- [Security Checklist](/docs/security-checklist.md)
- [Incident Response Procedures](/docs/runbook/incident-response.md)
- [AWS Secrets Manager Best Practices](https://docs.aws.amazon.com/secretsmanager/latest/userguide/best-practices.html)
