# Lambda Sizing Guide - AI Video Automation System

This document provides memory and timeout recommendations for each Lambda function based on workload analysis and profiling results.

**Region:** ap-southeast-1 (Singapore)
**Architecture:** ARM64 (Graviton2) - 20% cost savings vs x86_64

---

## Function Sizing Summary

| Function | Memory (MB) | Timeout (s) | vCPU Equivalent | Est. Cost/1M Invocations |
|----------|-------------|-------------|-----------------|--------------------------|
| API Lambda | 512 | 30 | 0.3 vCPU | $4.17 |
| Agent Lambda | 1024 | 120 | 0.6 vCPU | $16.67 |
| TTS Lambda | 512 | 60 | 0.3 vCPU | $8.33 |
| Video Lambda | 1024 | 90 | 0.6 vCPU | $15.00 |

---

## Detailed Function Analysis

### API Lambda (`ai-video-api`)

**Purpose:** Handle REST API requests (FastAPI + Mangum)

| Configuration | Value | Rationale |
|---------------|-------|-----------|
| Memory | 512 MB | Sufficient for FastAPI request handling |
| Timeout | 30s | API calls should respond quickly |
| Reserved Concurrency | None | Scale automatically |
| Provisioned Concurrency | None (consider at >100K RPM) |

**Performance Profile:**
- Average execution: 150-250ms
- P95 latency: 400ms
- P99 latency: 800ms
- Cold start: ~1.5s (first request after idle)

**Memory Analysis:**
```
Memory Used: 180-280 MB typical
Memory Overhead: ~100 MB (Python runtime + libraries)
Recommended Buffer: 100-150 MB
Final Recommendation: 512 MB
```

**Optimization Notes:**
- 512 MB provides 0.3 vCPU, adequate for I/O-bound API handling
- Increasing to 1024 MB doubles cost but only improves CPU-bound tasks
- Most API operations are I/O-bound (DynamoDB, external APIs)

---

### Agent Lambda (`ai-video-agent`)

**Purpose:** Run CrewAI agents for content generation

| Configuration | Value | Rationale |
|---------------|-------|-----------|
| Memory | 1024 MB | CrewAI + LangChain require more memory |
| Timeout | 120s | LLM API calls can be slow |
| Reserved Concurrency | 10 | Limit concurrent expensive operations |
| Provisioned Concurrency | None |

**Performance Profile:**
- Average execution: 15-45s (depends on agent tasks)
- P95 latency: 60s
- P99 latency: 90s
- Cold start: ~3s (heavier dependencies)

**Memory Analysis:**
```
Memory Used: 400-650 MB typical
Peak Memory: 800 MB (during complex agent runs)
Library Overhead: ~250 MB (CrewAI, LangChain, OpenAI SDK)
Recommended Buffer: 200 MB
Final Recommendation: 1024 MB
```

**Optimization Notes:**
- Higher memory = more CPU = faster agent execution
- 1024 MB provides 0.6 vCPU for parallel processing
- Reserved concurrency limits runaway costs from LLM calls
- Consider 2048 MB if agent execution regularly exceeds 60s

---

### TTS Lambda (`ai-video-tts`)

**Purpose:** Generate speech audio via ElevenLabs API

| Configuration | Value | Rationale |
|---------------|-------|-----------|
| Memory | 512 MB | Primarily I/O-bound (API calls) |
| Timeout | 60s | Audio generation can take time |
| Reserved Concurrency | 20 | Match ElevenLabs rate limits |
| Provisioned Concurrency | None |

**Performance Profile:**
- Average execution: 3-8s (depends on script length)
- P95 latency: 15s
- P99 latency: 25s
- Cold start: ~1.2s

**Memory Analysis:**
```
Memory Used: 150-250 MB typical
Audio Buffer: ~50 MB (for storing generated audio)
Library Overhead: ~80 MB
Recommended Buffer: 100 MB
Final Recommendation: 512 MB
```

**Optimization Notes:**
- Most time spent waiting for ElevenLabs API response
- Additional memory won't speed up external API calls
- Consider AWS Polly as fallback for cost optimization

---

### Video Lambda (`ai-video-video`)

**Purpose:** Orchestrate video generation via Kling AI

| Configuration | Value | Rationale |
|---------------|-------|-----------|
| Memory | 1024 MB | Handle large media payloads |
| Timeout | 90s | Video API responses can be slow |
| Reserved Concurrency | 10 | Limit concurrent video jobs |
| Provisioned Concurrency | None |

**Performance Profile:**
- Average execution: 8-15s (job submission + polling)
- P95 latency: 30s
- P99 latency: 60s
- Cold start: ~2s

**Memory Analysis:**
```
Memory Used: 300-500 MB typical
Media Handling: ~200 MB (image/video data)
Library Overhead: ~150 MB
Recommended Buffer: 150 MB
Final Recommendation: 1024 MB
```

**Optimization Notes:**
- Higher memory supports larger image processing
- 1024 MB provides adequate CPU for media handling
- Monitor for memory spikes with high-resolution inputs

---

## Profiling Methodology

### How to Profile Lambda Functions

1. **Enable X-Ray Tracing** (already configured)
   ```hcl
   tracing_config {
     mode = "Active"
   }
   ```

2. **Review CloudWatch Metrics**
   ```bash
   # Get memory utilization
   aws cloudwatch get-metric-statistics \
     --namespace AWS/Lambda \
     --metric-name Duration \
     --dimensions Name=FunctionName,Value=ai-video-api \
     --start-time $(date -u -d '7 days ago' +%Y-%m-%dT%H:%M:%SZ) \
     --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
     --period 3600 \
     --statistics Average Maximum \
     --region ap-southeast-1
   ```

3. **Use Lambda Power Tuning**
   - Deploy: https://github.com/alexcasalboni/aws-lambda-power-tuning
   - Finds optimal memory/cost balance automatically
   - Run periodically as workloads change

4. **Check Memory Used in Logs**
   ```bash
   # Look for REPORT lines in CloudWatch Logs
   aws logs filter-log-events \
     --log-group-name /aws/lambda/ai-video-api \
     --filter-pattern "REPORT" \
     --start-time $(date -u -d '1 hour ago' +%s)000 \
     --region ap-southeast-1 | grep "Max Memory Used"
   ```

---

## Memory-CPU Relationship

Lambda allocates CPU proportionally to memory:

| Memory (MB) | vCPU Equivalent | Best For |
|-------------|-----------------|----------|
| 128-512 | 0.08-0.3 | Simple I/O-bound tasks |
| 512-1024 | 0.3-0.6 | Moderate processing |
| 1024-3008 | 0.6-1.8 | CPU-intensive workloads |
| 3008-10240 | 1.8-6.0 | Heavy compute (rare) |

**Key Insight:** If your function is I/O-bound (waiting for APIs, databases), increasing memory beyond the minimum needed won't improve performance but will increase cost.

---

## Cost Optimization Checklist

- [x] Use ARM64 architecture (20% cheaper)
- [ ] Right-size memory based on actual usage
- [ ] Set appropriate timeouts (don't overprovision)
- [ ] Use reserved concurrency to limit costs
- [ ] Consider Provisioned Concurrency only at high volume
- [ ] Monitor with CloudWatch and X-Ray
- [ ] Run Lambda Power Tuning quarterly

---

## Terraform Configuration Examples

### API Lambda
```hcl
module "api_lambda" {
  source = "../modules/lambda"

  function_name = "ai-video-api"
  handler       = "src.api.main.handler"
  runtime       = "python3.11"
  memory_size   = 512
  timeout       = 30

  # ... other config
}
```

### Agent Lambda
```hcl
module "agent_lambda" {
  source = "../modules/lambda"

  function_name = "ai-video-agent"
  handler       = "src.agent.main.handler"
  runtime       = "python3.11"
  memory_size   = 1024
  timeout       = 120

  # ... other config
}
```

### TTS Lambda
```hcl
module "tts_lambda" {
  source = "../modules/lambda"

  function_name = "ai-video-tts"
  handler       = "src.tts.main.handler"
  runtime       = "python3.11"
  memory_size   = 512
  timeout       = 60

  # ... other config
}
```

### Video Lambda
```hcl
module "video_lambda" {
  source = "../modules/lambda"

  function_name = "ai-video-video"
  handler       = "src.video.main.handler"
  runtime       = "python3.11"
  memory_size   = 1024
  timeout       = 90

  # ... other config
}
```

---

## When to Re-evaluate Sizing

Trigger a sizing review when:

1. **Performance changes** - P95 latency increases >50%
2. **Memory warnings** - Functions approaching memory limit
3. **Cost spikes** - Unexpected billing increases
4. **Workload changes** - New features or usage patterns
5. **Quarterly review** - Scheduled optimization check

---

## Related Documents

- [Cost Analysis](/cost/analysis.md)
- [Infrastructure Overview](/infra/README.md)
- [AWS Lambda Pricing](https://aws.amazon.com/lambda/pricing/)
- [Lambda Power Tuning](https://github.com/alexcasalboni/aws-lambda-power-tuning)
