# DynamoDB Cost Optimization - AI Video Automation System

This document outlines cost optimization strategies for DynamoDB tables in the AI Video Platform.

**Region:** ap-southeast-1 (Singapore)

---

## Current Configuration

### Tables Overview

| Table | Billing Mode | Hash Key | Range Key | GSIs | TTL |
|-------|--------------|----------|-----------|------|-----|
| ai-video-users | PAY_PER_REQUEST | user_id | - | email-index | No |
| ai-video-products | PAY_PER_REQUEST | user_id | product_id | - | No |
| ai-video-jobs | PAY_PER_REQUEST | user_id | job_id | status-index | Yes (expires_at) |

### Current Pricing (ap-southeast-1)

| Operation | On-Demand Cost |
|-----------|----------------|
| Write Request Unit (WRU) | $1.4846 per million |
| Read Request Unit (RRU) | $0.297 per million |
| Storage | $0.297 per GB-month |

---

## On-Demand vs Provisioned Capacity

### Current: On-Demand Billing

**Advantages:**
- No capacity planning needed
- Automatic scaling to handle traffic spikes
- Pay only for what you use
- Ideal for unpredictable workloads
- No throttling concerns

**Disadvantages:**
- Higher per-request cost (~7x more expensive than provisioned)
- Less predictable monthly costs
- No reserved capacity discounts

**Best For:**
- New applications with unknown traffic patterns
- Spiky or unpredictable workloads
- Development and testing environments
- Applications with infrequent access patterns

### When to Switch to Provisioned Capacity

Consider switching to provisioned capacity when:

1. **Consistent Traffic Patterns**
   - Traffic is predictable with minimal variation
   - Can forecast capacity needs accurately

2. **High Utilization (>25%)**
   - Consistently using more than 25% of provisioned capacity
   - Break-even point is approximately 14.4% utilization

3. **Cost Savings Priority**
   - Potential savings of 60-70% compared to on-demand
   - With Reserved Capacity: up to 77% savings

**Provisioned Capacity Pricing:**

| Capacity Type | Hourly Cost | Monthly Equivalent |
|---------------|-------------|-------------------|
| Write Capacity Unit (WCU) | $0.000793 | ~$0.57 |
| Read Capacity Unit (RCU) | $0.0001586 | ~$0.11 |

**Break-Even Analysis:**

```
On-Demand WRU: $1.4846 per million = $0.0000014846 per request
Provisioned WCU: $0.000793/hour = $0.00000022 per request (at 100% utilization)

Break-even: ~14.4% utilization
```

---

## Optimization Techniques

### 1. Use TTL for Auto-Deletion

TTL automatically deletes expired items at no cost, reducing storage and avoiding manual cleanup.

**Currently Enabled:**
- Jobs table: `expires_at` attribute

**Recommended TTL Settings:**

| Table | TTL Attribute | Retention Period | Rationale |
|-------|---------------|------------------|-----------|
| jobs | expires_at | 30 days | Completed jobs rarely accessed after |
| products | - | Consider adding | Remove deleted/archived products |

**Implementation:**
```python
# When creating a job, set expires_at
from datetime import datetime, timedelta

expires_at = int((datetime.utcnow() + timedelta(days=30)).timestamp())
job_item = {
    "user_id": user_id,
    "job_id": job_id,
    "expires_at": expires_at,  # DynamoDB TTL
    # ... other attributes
}
```

### 2. Use Sparse Indexes

Only index attributes that have values. DynamoDB doesn't write items to GSI if the indexed attribute is missing.

**Current GSIs:**
- `email-index` on users table (always populated - OK)
- `status-index` on jobs table (always populated - OK)

**Best Practice:**
```python
# Don't include optional attributes in GSI if not needed for queries
# Only add indexed attribute when it has a meaningful value
```

### 3. Compress Large Attributes

For attributes larger than 1KB, consider compression to reduce storage and RCU/WCU consumption.

**When to Compress:**
- Script content (can be 2-5KB)
- Metadata JSON blobs
- Error messages/stack traces

**Implementation:**
```python
import gzip
import base64

def compress_attribute(data: str) -> str:
    """Compress large string attributes."""
    if len(data) < 1024:  # Only compress if > 1KB
        return data
    compressed = gzip.compress(data.encode('utf-8'))
    return base64.b64encode(compressed).decode('utf-8')

def decompress_attribute(data: str) -> str:
    """Decompress attribute if compressed."""
    try:
        decoded = base64.b64decode(data)
        return gzip.decompress(decoded).decode('utf-8')
    except Exception:
        return data  # Not compressed, return as-is
```

### 4. Batch Operations

Use batch operations to reduce request overhead and improve throughput.

**BatchWriteItem:**
- Up to 25 items per request
- Up to 16MB total request size
- Reduces per-item overhead

**BatchGetItem:**
- Up to 100 items per request
- Up to 16MB total response size

**Implementation:**
```python
# Instead of multiple put_item calls
for item in items:
    table.put_item(Item=item)  # N requests

# Use batch_write_item
with table.batch_writer() as batch:
    for item in items:
        batch.put_item(Item=item)  # Batched into ceil(N/25) requests
```

### 5. Optimize Item Size

DynamoDB charges based on item size rounded up to the nearest 1KB (for writes) or 4KB (for eventually consistent reads).

**Strategies:**
- Use short attribute names in high-volume tables
- Store large blobs in S3, reference by key
- Remove redundant/derived attributes

**Example:**
```python
# Before (verbose)
{
    "user_identifier": "...",
    "product_identifier": "...",
    "creation_timestamp": "...",
    "modification_timestamp": "..."
}

# After (optimized)
{
    "uid": "...",
    "pid": "...",
    "cat": "...",  # created_at
    "uat": "..."   # updated_at
}
```

### 6. Use Eventually Consistent Reads

Eventually consistent reads cost half as much as strongly consistent reads.

**When to Use:**
- Displaying lists/dashboards
- Analytics queries
- Non-critical data display

**When NOT to Use:**
- Immediately after writes
- Financial/critical operations
- Authentication checks

**Implementation:**
```python
# Eventually consistent (default, cheaper)
response = table.get_item(
    Key={'user_id': user_id},
    ConsistentRead=False  # Default
)

# Strongly consistent (2x cost)
response = table.get_item(
    Key={'user_id': user_id},
    ConsistentRead=True
)
```

### 7. Project Only Required Attributes

Use projection expressions to retrieve only needed attributes.

**Implementation:**
```python
# Retrieve all attributes (wasteful)
response = table.get_item(Key={'user_id': user_id})

# Retrieve only needed attributes (optimized)
response = table.get_item(
    Key={'user_id': user_id},
    ProjectionExpression='user_id, email, #s',
    ExpressionAttributeNames={'#s': 'status'}
)
```

---

## Monitoring and Alerts

### CloudWatch Metrics to Monitor

| Metric | Threshold | Action |
|--------|-----------|--------|
| ConsumedReadCapacityUnits | >80% provisioned | Consider scaling up |
| ConsumedWriteCapacityUnits | >80% provisioned | Consider scaling up |
| ThrottledRequests | >0 | Investigate immediately |
| UserErrors | >1% of requests | Review application code |

### Cost Monitoring Query

```bash
# Check DynamoDB costs for last 7 days
aws ce get-cost-and-usage \
  --time-period Start=$(date -u -d '7 days ago' +%Y-%m-%d),End=$(date -u +%Y-%m-%d) \
  --granularity DAILY \
  --filter '{"Dimensions": {"Key": "SERVICE", "Values": ["Amazon DynamoDB"]}}' \
  --metrics BlendedCost \
  --region ap-southeast-1
```

---

## Migration Path: On-Demand to Provisioned

If traffic becomes predictable, follow this migration path:

### Step 1: Analyze Current Usage (2-4 weeks)

```bash
# Get consumed capacity metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/DynamoDB \
  --metric-name ConsumedWriteCapacityUnits \
  --dimensions Name=TableName,Value=ai-video-jobs \
  --start-time $(date -u -d '7 days ago' +%Y-%m-%dT%H:%M:%SZ) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%SZ) \
  --period 3600 \
  --statistics Average Maximum \
  --region ap-southeast-1
```

### Step 2: Calculate Required Capacity

```
Average WCU = ConsumedWriteCapacityUnits / 3600
Peak WCU = Maximum ConsumedWriteCapacityUnits / 3600
Provisioned WCU = Peak WCU * 1.2 (20% buffer)
```

### Step 3: Enable Auto Scaling

```hcl
# Terraform configuration for auto-scaling
resource "aws_appautoscaling_target" "jobs_write" {
  max_capacity       = 100
  min_capacity       = 5
  resource_id        = "table/${aws_dynamodb_table.jobs.name}"
  scalable_dimension = "dynamodb:table:WriteCapacityUnits"
  service_namespace  = "dynamodb"
}

resource "aws_appautoscaling_policy" "jobs_write_policy" {
  name               = "DynamoDBWriteAutoScaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.jobs_write.resource_id
  scalable_dimension = aws_appautoscaling_target.jobs_write.scalable_dimension
  service_namespace  = aws_appautoscaling_target.jobs_write.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "DynamoDBWriteCapacityUtilization"
    }
    target_value = 70.0
  }
}
```

### Step 4: Switch Billing Mode

```hcl
resource "aws_dynamodb_table" "jobs" {
  # Change from PAY_PER_REQUEST to PROVISIONED
  billing_mode   = "PROVISIONED"
  read_capacity  = 10
  write_capacity = 10

  # ... rest of configuration
}
```

---

## Cost Projection

### Current Estimated Costs (On-Demand)

| Table | Est. RRU/month | Est. WRU/month | Est. Cost |
|-------|----------------|----------------|-----------|
| users | 50,000 | 10,000 | ~$0.03 |
| products | 100,000 | 20,000 | ~$0.06 |
| jobs | 200,000 | 50,000 | ~$0.13 |
| **Total** | | | **~$0.22/month** |

### Projected with Provisioned Capacity

| Table | RCU | WCU | Est. Cost |
|-------|-----|-----|-----------|
| users | 2 | 1 | ~$0.79 |
| products | 5 | 2 | ~$1.70 |
| jobs | 10 | 5 | ~$3.95 |
| **Total** | | | **~$6.44/month** |

**Recommendation:** Stay with on-demand billing until traffic increases significantly. Current usage is well within on-demand cost efficiency zone.

---

## Related Documents

- [Cost Analysis](/cost/analysis.md)
- [Lambda Sizing Guide](/docs/cost/lambda-sizing.md)
- [AWS DynamoDB Pricing](https://aws.amazon.com/dynamodb/pricing/)
- [DynamoDB Best Practices](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/best-practices.html)
