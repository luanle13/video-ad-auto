# Logging Security Audit - AI Video Automation System

This document audits the logging practices across the application to ensure sensitive data is not exposed in logs.

---

## Current Logging Review

### Safe to Log

The following data types are safe to include in log entries:

| Field | Example | Notes |
|-------|---------|-------|
| `user_id` | `user-abc123` | UUID, non-PII |
| `job_id` | `job-xyz789` | UUID, non-PII |
| `product_id` | `prod-def456` | UUID, non-PII |
| `timestamps` | `2024-01-15T10:30:00Z` | ISO format |
| `status` | `PROCESSING`, `COMPLETE` | Enum values |
| `error_code` | `NOT_FOUND`, `VALIDATION_ERROR` | Error codes only |
| `environment` | `dev`, `prod` | Environment name |
| `bucket` | `ai-video-images` | S3 bucket names |
| `key` | `user-id/product-id/file.jpg` | S3 keys (no secrets) |
| `service_name` | `ElevenLabs`, `Kling` | Service identifiers |
| `task` | `analyze`, `generate` | Task names |
| `step_name` | `script_generation` | Pipeline steps |

### Must NOT Log

The following sensitive data types must NEVER appear in logs:

| Field | Risk | Mitigation |
|-------|------|------------|
| `password` | Credential exposure | Never log, use `***REDACTED***` |
| `api_key` | API key exposure | Never log, mask completely |
| `access_token` | Session hijacking | Never log, use `***TOKEN***` |
| `refresh_token` | Session hijacking | Never log, use `***TOKEN***` |
| `secret_key` | Credential exposure | Never log, mask completely |
| `email` | PII exposure | Hash or mask: `u***@example.com` |
| `phone` | PII exposure | Mask: `***-***-1234` |
| Request bodies with passwords | Credential exposure | Sanitize before logging |
| Full exception traces with secrets | Credential exposure | Filter sensitive data |

---

## Current Issues Identified

### High Priority

1. **Email addresses logged in plaintext**
   - Location: `src/api/routes/auth.py:44` - `logger.info("user_registered", email=request.email)`
   - Location: `src/api/routes/auth.py:66` - `logger.info("user_logged_in", email=request.email)`
   - Location: `src/shared/db.py:63` - `logger.info("user_created", email=email)`
   - Risk: PII exposure in CloudWatch logs
   - Fix: Hash or mask email addresses

### Medium Priority

2. **Credentials logging in credentials route**
   - Location: `src/api/routes/credentials.py:50`
   - Review: Ensure no access tokens are logged
   - Status: Currently logging user_id and platform only (OK)

3. **Token validation logging**
   - Location: `src/api/dependencies/auth.py:69`
   - Review: Ensure full tokens are not logged in error messages
   - Status: Currently logging generic "invalid_token" (OK)

---

## Recommendations

### 1. Add Log Sanitization Middleware

Implement automatic sanitization in the logging module to mask sensitive patterns:

```python
SENSITIVE_PATTERNS = {
    "email": mask_email,      # user@example.com -> u***@example.com
    "password": mask_secret,  # any value -> ***REDACTED***
    "token": mask_token,      # jwt.token.here -> ***TOKEN***
    "api_key": mask_secret,   # sk-abc123 -> ***REDACTED***
    "secret": mask_secret,    # any secret -> ***REDACTED***
}
```

### 2. Mask Sensitive Fields in Structured Logs

Add a structlog processor to automatically sanitize log event dictionaries:

- Scan all log fields for sensitive key patterns
- Apply appropriate masking function
- Preserve log structure for debugging

### 3. Review CloudWatch Log Retention

| Log Group | Current Retention | Recommended |
|-----------|-------------------|-------------|
| API Lambda | 30 days | 90 days |
| Worker Lambdas | 30 days | 90 days |
| Agent Lambda | 30 days | 90 days |

Ensure logs containing potentially sensitive data are not retained indefinitely.

### 4. Log Access Controls

- Restrict CloudWatch log access to authorized personnel only
- Enable CloudWatch Logs encryption with KMS
- Audit log access via CloudTrail

---

## Sensitive Field Patterns

The following regex patterns identify sensitive data:

| Pattern | Regex | Description |
|---------|-------|-------------|
| Email | `[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}` | Email addresses |
| JWT Token | `eyJ[a-zA-Z0-9_-]+\.eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+` | JWT tokens |
| API Key (generic) | `(sk|pk|api)[_-]?[a-zA-Z0-9]{20,}` | API keys |
| AWS Key | `AKIA[0-9A-Z]{16}` | AWS access keys |

---

## Implementation Checklist

- [x] Create sanitization functions in `logging.py`
- [x] Add structlog processor for automatic sanitization
- [ ] Update auth routes to use masked email logging
- [ ] Review all logger calls for sensitive data
- [ ] Configure CloudWatch log encryption
- [ ] Set appropriate log retention policies
- [ ] Document logging standards for developers

---

## Testing

After implementing sanitization:

1. Verify emails are masked in log output
2. Verify tokens/passwords never appear in logs
3. Test that log structure is preserved
4. Verify sanitization works in both dev and prod modes

---

## Related Documents

- [Input Validation Audit](/security/input-validation.md)
- [Secrets Rotation Procedure](/docs/runbook/secrets-rotation.md)
- [AWS CloudWatch Logs Best Practices](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/BestPractices.html)
