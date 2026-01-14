# Cost Analysis - AI Video Automation System

This document provides cost estimates and optimization strategies for the AI Video Platform.

**Region:** ap-southeast-1 (Singapore)
**Pricing Date:** January 2025

---

## Current Architecture Costs (Estimated Monthly)

### Compute - AWS Lambda

| Component | Memory | Avg Duration | Est. Invocations/month | Est. Cost |
|-----------|--------|--------------|------------------------|-----------|
| API Lambda | 512 MB | 200ms | 50,000 | $5-10 |
| Agent Lambda | 1024 MB | 30s | 2,000 | $10-20 |
| TTS Lambda | 512 MB | 5s | 2,000 | $5-10 |
| Video Lambda | 1024 MB | 10s | 2,000 | $10-20 |

**Subtotal:** $30-60/month

**Calculation Notes:**
- Lambda pricing: $0.0000166667 per GB-second
- First 1M requests free, then $0.20 per 1M requests
- Agent Lambda has longer duration due to LLM API calls

---

### Storage

#### DynamoDB (On-Demand)

| Table | Avg Item Size | Est. RCU/month | Est. WCU/month | Est. Cost |
|-------|---------------|----------------|----------------|-----------|
| ai-video-users | 500 bytes | 50,000 | 10,000 | $1-2 |
| ai-video-products | 2 KB | 100,000 | 20,000 | $2-4 |
| ai-video-jobs | 1 KB | 200,000 | 50,000 | $2-4 |

**Subtotal:** $5-10/month

**Pricing:**
- On-demand read: $0.25 per million RCU
- On-demand write: $1.25 per million WCU
- Storage: $0.25 per GB-month

#### S3 Storage

| Bucket | Est. Storage | Est. Requests | Lifecycle | Est. Cost |
|--------|--------------|---------------|-----------|-----------|
| Images | 10 GB | 50,000 GET, 10,000 PUT | None | $1-2 |
| Videos | 50 GB | 20,000 GET, 5,000 PUT | 90-day delete | $5-10 |

**Subtotal:** $6-12/month

**Pricing:**
- S3 Standard: $0.025 per GB-month
- PUT/POST: $0.005 per 1,000 requests
- GET: $0.0004 per 1,000 requests

---

### External API Costs

#### OpenAI GPT-4.1 (CrewAI Agents)

| Usage Type | Est. Tokens/Video | Est. Videos/month | Token Cost | Est. Cost |
|------------|-------------------|-------------------|------------|-----------|
| Input tokens | 2,000 | 2,000 | $0.01/1K | $40 |
| Output tokens | 1,000 | 2,000 | $0.03/1K | $60 |

**Subtotal:** $80-120/month (main cost driver)

**Notes:**
- GPT-4.1 pricing: $0.01/1K input, $0.03/1K output
- Can optimize with prompt caching and shorter prompts
- Consider GPT-4o-mini for cost reduction (~10x cheaper)

#### ElevenLabs TTS

| Plan | Characters/month | Cost |
|------|------------------|------|
| Free | 10,000 | $0 |
| Starter | 30,000 | $5 |
| Creator | 100,000 | $22 |
| Pro | 500,000 | $99 |

**Subtotal:** $5-22/month (based on plan)

**Notes:**
- ~500 characters per 30-second video script
- Starter plan covers ~60 videos/month
- Creator plan covers ~200 videos/month

#### Kling AI Video Generation

| Tier | Videos/month | Est. Cost |
|------|--------------|-----------|
| Pay-as-you-go | 50 | $20 |
| Basic Plan | 100 | $35 |
| Pro Plan | 500 | $99 |

**Subtotal:** $20-50/month (based on usage)

**Notes:**
- Pricing varies by video length and quality
- 30-second videos at standard quality assumed
- Consider caching/reusing generated segments

---

### Networking & API Gateway

| Service | Est. Usage | Est. Cost |
|---------|------------|-----------|
| API Gateway | 500K requests | $3-5 |
| CloudFront | 100 GB transfer | $1-5 |
| Data Transfer (out) | 50 GB | $5-10 |

**Subtotal:** $9-20/month

---

### Security & Monitoring

| Service | Est. Usage | Est. Cost |
|---------|------------|-----------|
| Cognito | 1,000 MAU | $0 (free tier) |
| Secrets Manager | 5 secrets | $2 |
| CloudWatch Logs | 10 GB | $5 |
| CloudWatch Metrics | Standard | $0 |
| X-Ray | 100K traces | $0.50 |

**Subtotal:** $7-10/month

---

### Orchestration

| Service | Est. Usage | Est. Cost |
|---------|------------|-----------|
| Step Functions | 5,000 transitions | $1-2 |

**Subtotal:** $1-2/month

---

## Total Cost Summary

| Category | Low Estimate | High Estimate |
|----------|--------------|---------------|
| AWS Lambda | $30 | $60 |
| DynamoDB | $5 | $10 |
| S3 Storage | $6 | $12 |
| OpenAI API | $80 | $120 |
| ElevenLabs | $5 | $22 |
| Kling AI | $20 | $50 |
| Networking | $9 | $20 |
| Security/Monitoring | $7 | $10 |
| Step Functions | $1 | $2 |

### **Total Estimated: $163-306/month**

---

## Per-Video Cost Breakdown

Assuming 2,000 videos/month:

| Component | Cost per Video |
|-----------|----------------|
| OpenAI (GPT-4.1) | $0.05-0.06 |
| ElevenLabs TTS | $0.01-0.03 |
| Kling AI Video | $0.04-0.10 |
| Lambda Compute | $0.01-0.02 |
| Storage & Transfer | $0.01 |
| Other AWS Services | $0.01 |

### **Per-Video Cost: $0.13-0.23**

---

## Cost Optimization Strategies

### Immediate Optimizations

1. **Use GPT-4o-mini for non-critical tasks**
   - 10x cheaper than GPT-4.1
   - Good for simple script generation
   - Savings: ~$60-80/month

2. **Implement prompt caching**
   - Cache system prompts and examples
   - Reduce input token count by 30-50%
   - Savings: ~$15-25/month

3. **S3 Lifecycle policies**
   - Delete videos after 90 days
   - Move to Glacier after 30 days
   - Savings: ~$3-5/month

4. **Use AWS Polly fallback strategically**
   - Polly is ~$4 per 1M characters
   - Use for bulk/non-premium videos
   - Savings: ~$10-15/month if 50% use Polly

### Medium-term Optimizations

1. **Lambda Provisioned Concurrency**
   - Reduces cold starts
   - Only cost-effective at high volume (>100K requests/month)

2. **Reserved Capacity for DynamoDB**
   - 70% discount vs on-demand
   - Only worthwhile with predictable traffic

3. **CloudFront caching**
   - Cache generated videos
   - Reduce S3 GET requests and data transfer

4. **Batch processing**
   - Process multiple videos in single Lambda invocation
   - Reduce invocation overhead

### Long-term Optimizations

1. **Self-hosted LLM (if volume justifies)**
   - Consider Llama 3 on SageMaker
   - Break-even at ~$500/month LLM spend

2. **Custom TTS model**
   - Train on specific voice style
   - High upfront cost, low marginal cost

3. **Video generation optimization**
   - Template-based video assembly
   - Reduce Kling AI calls for similar products

---

## Cost Monitoring

### CloudWatch Alarms

Set up billing alarms at these thresholds:

| Threshold | Action |
|-----------|--------|
| $50/month | Monitor - review usage |
| $150/month | Warning - investigate spikes |
| $300/month | Alert - immediate review |
| $500/month | Critical - potential issue |

### Cost Allocation Tags

Apply these tags to all resources:

```
Project: ai-video-platform
Environment: prod/dev
Component: api/agent/tts/video
Owner: platform-team
```

### Monthly Review Checklist

- [ ] Review AWS Cost Explorer by service
- [ ] Check external API usage (OpenAI, ElevenLabs, Kling)
- [ ] Identify unused resources
- [ ] Review Lambda memory/duration metrics
- [ ] Check S3 storage growth
- [ ] Validate DynamoDB capacity usage

---

## Scaling Projections

| Videos/month | Est. Monthly Cost | Cost/Video |
|--------------|-------------------|------------|
| 500 | $100-150 | $0.20-0.30 |
| 2,000 | $160-300 | $0.08-0.15 |
| 10,000 | $500-800 | $0.05-0.08 |
| 50,000 | $1,500-2,500 | $0.03-0.05 |

**Note:** Per-video cost decreases at scale due to fixed costs being amortized and volume discounts from API providers.

---

## Free Tier Utilization

Current free tier benefits (first 12 months):

| Service | Free Tier | Est. Savings |
|---------|-----------|--------------|
| Lambda | 1M requests, 400K GB-seconds | $10-15/month |
| API Gateway | 1M calls | $3-4/month |
| DynamoDB | 25 RCU, 25 WCU | $5-10/month |
| S3 | 5 GB storage, 20K GET | $1-2/month |
| CloudWatch | 10 metrics, 5 GB logs | $2-3/month |
| Cognito | 50K MAU | $0 |

**Total Free Tier Savings:** ~$20-35/month (first year)

---

## Related Documents

- [Infrastructure Overview](/infra/README.md)
- [Performance Optimization](/docs/performance.md)
- [AWS Well-Architected Cost Optimization](https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/welcome.html)
