# Incident Response Runbook - AI Video Automation System

This document outlines the procedures for responding to incidents affecting the AI Video Platform.

---

## Severity Levels

### Critical (P1)

**Definition:** Complete service outage or security emergency requiring immediate response.

| Criteria | Examples |
|----------|----------|
| Service completely down | API returning 5xx for all requests |
| Data breach suspected | Unauthorized data access detected |
| Security vulnerability exploited | Active attack in progress |
| Customer data exposed | PII leaked to unauthorized parties |
| All video generation failing | Step Functions executions all failing |

**Response Time:** Acknowledge within 15 minutes, resolve within 4 hours.

---

### High (P2)

**Definition:** Major functionality impaired, significant user impact.

| Criteria | Examples |
|----------|----------|
| Major feature broken | Video generation failing for 50%+ of jobs |
| Performance severely degraded | API latency > 10x normal |
| API key compromised | Third-party key exposed (Kling, ElevenLabs) |
| Authentication failing | Cognito integration broken |
| Database connectivity issues | DynamoDB throttling or errors |

**Response Time:** Acknowledge within 30 minutes, resolve within 8 hours.

---

### Medium (P3)

**Definition:** Minor functionality impaired, limited user impact.

| Criteria | Examples |
|----------|----------|
| Minor feature broken | Single TTS voice not working |
| Intermittent errors | Occasional 500 errors (< 5% of requests) |
| Non-critical integration issue | Analytics not collecting |
| UI rendering issues | Frontend display problems |
| Slow performance | Response times 2-3x normal |

**Response Time:** Acknowledge within 2 hours, resolve within 24 hours.

---

### Low (P4)

**Definition:** Minimal impact, cosmetic issues, or feature requests.

| Criteria | Examples |
|----------|----------|
| Cosmetic issues | Typos, UI alignment |
| Documentation gaps | Missing or outdated docs |
| Non-urgent improvements | Performance optimization opportunities |

**Response Time:** Acknowledge within 1 business day, schedule for next sprint.

---

## Response Procedures

### P1 Critical Response

#### Immediate Actions (0-15 minutes)

1. **Acknowledge the incident**
   - Respond in incident channel: `#incidents`
   - Create incident ticket with severity tag
   - Start incident timer

2. **Assemble incident team**
   - Page on-call engineer (primary)
   - Notify security lead (if security-related)
   - Notify engineering manager

3. **Initial assessment**
   ```bash
   # Check service health
   curl -s https://api.your-domain.com/health | jq

   # Check CloudWatch for error spikes
   aws cloudwatch get-metric-statistics \
     --namespace AWS/Lambda \
     --metric-name Errors \
     --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ) \
     --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
     --period 300 \
     --statistics Sum \
     --region ap-southeast-1
   ```

4. **Communicate status**
   - Send initial notification to stakeholders
   - Update status page (if applicable)

#### Investigation (15-60 minutes)

1. **Gather evidence**
   - CloudWatch Logs for affected services
   - X-Ray traces for failed requests
   - DynamoDB metrics for database issues
   - Step Functions execution history

2. **Identify root cause**
   - Review recent deployments
   - Check for external service outages
   - Analyze error patterns

3. **Status updates every 30 minutes**
   - Use status update template
   - Include current findings
   - Estimated time to resolution

#### Resolution

1. **Implement fix or rollback**
   ```bash
   # Rollback Lambda to previous version
   aws lambda update-alias \
     --function-name video-platform-api \
     --name prod \
     --function-version PREVIOUS_VERSION \
     --region ap-southeast-1
   ```

2. **Verify fix**
   - Run smoke tests
   - Monitor error rates
   - Confirm user reports resolved

3. **Close incident**
   - Send resolution notification
   - Update ticket status
   - Schedule post-incident review

#### Post-Incident (within 48 hours)

1. **Conduct post-incident review (PIR)**
   - Timeline of events
   - Root cause analysis
   - Impact assessment
   - Action items

2. **Document findings**
   - Update runbooks if needed
   - Create follow-up tickets
   - Share learnings with team

---

### P2 High Response

#### Actions (0-30 minutes)

1. **Acknowledge in incident channel**
2. **Assess impact scope**
3. **Notify affected team members**
4. **Begin investigation**

#### Investigation

1. **Review logs and metrics**
2. **Identify affected components**
3. **Determine if rollback needed**

#### Resolution

1. **Implement fix or workaround**
2. **Verify resolution**
3. **Document in ticket**

---

### P3/P4 Response

1. **Create ticket with appropriate priority**
2. **Assign to relevant team member**
3. **Schedule for appropriate sprint/timeline**
4. **Communicate ETA to reporter**

---

## Security Incident Response

### If Data Breach Suspected

1. **Preserve evidence**
   - Do NOT modify logs or systems
   - Enable enhanced logging
   - Capture current state

2. **Contain the breach**
   - Rotate compromised credentials immediately
   - Revoke suspicious sessions
   - Block malicious IPs if identified

3. **Notify security team immediately**
   - Email: security@company.com
   - Phone: [Security Lead Phone]

4. **Legal/Compliance notification**
   - May be required within 72 hours depending on jurisdiction
   - Document all actions taken

### If API Key Compromised

1. **Rotate key immediately** (see [Secrets Rotation](/docs/runbook/secrets-rotation.md))
2. **Review usage logs for unauthorized access**
3. **Assess data exposure**
4. **Notify affected service provider**

---

## Contact List

### On-Call Rotation

| Role | Primary | Secondary | Escalation |
|------|---------|-----------|------------|
| Platform Engineer | [Name] | [Name] | [Name] |
| Security Lead | [Name] | [Name] | [Name] |
| Engineering Manager | [Name] | - | [VP Engineering] |

### Contact Information

| Role | Email | Phone | Slack |
|------|-------|-------|-------|
| On-Call | oncall@company.com | [Phone] | @oncall |
| Security | security@company.com | [Phone] | @security-team |
| Engineering Manager | eng-manager@company.com | [Phone] | @eng-manager |

### External Contacts

| Service | Support URL | Support Email |
|---------|-------------|---------------|
| AWS | https://console.aws.amazon.com/support | - |
| Kling AI | [Support URL] | [Support Email] |
| ElevenLabs | https://elevenlabs.io/contact | - |
| OpenAI | https://help.openai.com | - |

---

## Communication Templates

### Initial Notification Template

```
INCIDENT ALERT - [P1/P2/P3] - [Brief Description]

Time Detected: [YYYY-MM-DD HH:MM UTC]
Severity: [P1 Critical / P2 High / P3 Medium]
Status: Investigating

Impact:
- [Describe user impact]
- [Affected features/services]

Current Actions:
- [Action being taken]
- [Who is responding]

Next Update: [Time]

Incident Commander: [Name]
```

### Status Update Template

```
INCIDENT UPDATE - [P1/P2/P3] - [Brief Description]

Time: [YYYY-MM-DD HH:MM UTC]
Status: [Investigating / Identified / Monitoring / Resolved]

Summary:
[1-2 sentence summary of current state]

Findings:
- [Key finding 1]
- [Key finding 2]

Actions Taken:
- [Action 1]
- [Action 2]

Next Steps:
- [Planned action 1]
- [Planned action 2]

Estimated Resolution: [Time or "Investigating"]

Next Update: [Time]
```

### Resolution Template

```
INCIDENT RESOLVED - [P1/P2/P3] - [Brief Description]

Resolved At: [YYYY-MM-DD HH:MM UTC]
Duration: [X hours Y minutes]

Root Cause:
[Brief description of what caused the incident]

Resolution:
[What was done to fix it]

Impact Summary:
- Users affected: [Number or "All" / "None"]
- Feature(s) impacted: [List]
- Data impact: [None / Describe if any]

Follow-up Actions:
- [ ] Post-incident review scheduled for [Date]
- [ ] [Other follow-up items]

Incident Commander: [Name]
```

---

## Useful Commands

### Check Lambda Errors

```bash
# View recent errors
aws logs filter-log-events \
  --log-group-name /aws/lambda/video-platform-api \
  --filter-pattern "ERROR" \
  --start-time $(date -u -d '1 hour ago' +%s)000 \
  --region ap-southeast-1

# Tail logs in real-time
aws logs tail /aws/lambda/video-platform-api --follow --region ap-southeast-1
```

### Check Step Functions

```bash
# List failed executions
aws stepfunctions list-executions \
  --state-machine-arn arn:aws:states:ap-southeast-1:ACCOUNT:stateMachine:video-pipeline \
  --status-filter FAILED \
  --max-results 10 \
  --region ap-southeast-1
```

### Check DynamoDB

```bash
# Check table status
aws dynamodb describe-table --table-name ai-video-jobs --region ap-southeast-1

# Check consumed capacity
aws cloudwatch get-metric-statistics \
  --namespace AWS/DynamoDB \
  --metric-name ConsumedReadCapacityUnits \
  --dimensions Name=TableName,Value=ai-video-jobs \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --period 300 \
  --statistics Sum \
  --region ap-southeast-1
```

### Rollback Deployment

```bash
# List Lambda versions
aws lambda list-versions-by-function \
  --function-name video-platform-api \
  --region ap-southeast-1

# Update alias to previous version
aws lambda update-alias \
  --function-name video-platform-api \
  --name prod \
  --function-version PREVIOUS_VERSION \
  --region ap-southeast-1
```

---

## Escalation Matrix

| Time Elapsed | Action |
|--------------|--------|
| 0 min | Primary on-call notified |
| 15 min (P1) / 30 min (P2) | Secondary on-call notified if no response |
| 30 min (P1) / 1 hour (P2) | Engineering manager notified |
| 1 hour (P1) | VP Engineering notified |
| 2 hours (P1) | Executive team notified |

---

## Related Documents

- [Secrets Rotation Procedure](/docs/runbook/secrets-rotation.md)
- [Security Checklist](/security/checklist.md)
- [Logging Audit](/security/logging-audit.md)
- [AWS Well-Architected - Reliability Pillar](https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/welcome.html)
