# IAM Policy Audit

## Executive Summary

This document audits IAM policies for the AI Video Automation System. The audit identifies current permissions, required permissions per Lambda function, security concerns, and recommendations for achieving least-privilege access.

**Audit Date:** 2026-01-12
**Region:** ap-southeast-1
**Status:** Action Required

### Key Findings

| Severity | Finding | Location |
|----------|---------|----------|
| HIGH | Single shared Lambda role for all functions | `infra/modules/lambda/iam.tf` |
| MEDIUM | Polly uses wildcard resource `*` | `infra/modules/lambda/policies.tf:134` |
| MEDIUM | Step Functions CloudWatch Logs uses `*` | `infra/modules/stepfunctions/main.tf:55` |
| LOW | Step Functions X-Ray uses `*` | `infra/modules/stepfunctions/main.tf:65` |
| HIGH | Lambda module policies not wired in main.tf | `infra/main.tf` |

---

## Current IAM Architecture

### Lambda Execution Role

**Resource:** `aws_iam_role.lambda_role`
**File:** `infra/modules/lambda/iam.tf`

All four Lambda functions currently share a single IAM role:
- `lambda_api` - API handler
- `lambda_agents` - AI agents handler
- `lambda_tts` - Text-to-speech handler
- `lambda_video` - Video generation handler

#### Attached Policies

| Policy | Type | Purpose |
|--------|------|---------|
| `AWSLambdaBasicExecutionRole` | AWS Managed | CloudWatch Logs |
| `AWSXRayDaemonWriteAccess` | AWS Managed | X-Ray tracing |
| Custom CloudWatch policy | Inline | Log group management |

#### Conditional Policies (Module Supports)

The Lambda module defines conditional policies that attach based on variables passed during instantiation:

```hcl
# DynamoDB - attaches if dynamodb_table_arns provided
# S3 - attaches if s3_bucket_arns provided
# Secrets Manager - attaches if secrets_arns provided
# Step Functions - attaches if sfn_arns provided
# Polly - attaches if polly_access = true
```

**Current Issue:** These variables are NOT being passed in `infra/main.tf`, so Lambda functions lack necessary permissions.

---

## Lambda Roles - Required Permissions

### API Lambda (`lambda_api`)

Handles REST API requests, project CRUD operations, and pipeline initiation.

#### Required Permissions

| Service | Actions | Resource Scope |
|---------|---------|----------------|
| DynamoDB | `GetItem`, `PutItem`, `UpdateItem`, `DeleteItem`, `Query` | Projects table ARN |
| S3 | `GetObject`, `PutObject` | Assets bucket ARN/* |
| Secrets Manager | `GetSecretValue` | OpenAI API key secret ARN |
| Step Functions | `StartExecution` | Video pipeline state machine ARN |

#### Recommended Policy

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DynamoDBAccess",
      "Effect": "Allow",
      "Action": [
        "dynamodb:GetItem",
        "dynamodb:PutItem",
        "dynamodb:UpdateItem",
        "dynamodb:DeleteItem",
        "dynamodb:Query"
      ],
      "Resource": [
        "arn:aws:dynamodb:ap-southeast-1:${ACCOUNT_ID}:table/${PROJECTS_TABLE}",
        "arn:aws:dynamodb:ap-southeast-1:${ACCOUNT_ID}:table/${PROJECTS_TABLE}/index/*"
      ]
    },
    {
      "Sid": "S3Access",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject"
      ],
      "Resource": "arn:aws:s3:::${ASSETS_BUCKET}/*"
    },
    {
      "Sid": "SecretsAccess",
      "Effect": "Allow",
      "Action": "secretsmanager:GetSecretValue",
      "Resource": "arn:aws:secretsmanager:ap-southeast-1:${ACCOUNT_ID}:secret:video-ad-auto/openai-*"
    },
    {
      "Sid": "StepFunctionsAccess",
      "Effect": "Allow",
      "Action": "states:StartExecution",
      "Resource": "arn:aws:states:ap-southeast-1:${ACCOUNT_ID}:stateMachine:video-generation-pipeline"
    }
  ]
}
```

---

### Agent Lambda (`lambda_agents`)

Executes CrewAI agents for script generation.

#### Required Permissions

| Service | Actions | Resource Scope |
|---------|---------|----------------|
| DynamoDB | `UpdateItem` | Projects table ARN |
| Secrets Manager | `GetSecretValue` | OpenAI API key secret ARN |

#### Recommended Policy

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DynamoDBAccess",
      "Effect": "Allow",
      "Action": "dynamodb:UpdateItem",
      "Resource": "arn:aws:dynamodb:ap-southeast-1:${ACCOUNT_ID}:table/${PROJECTS_TABLE}"
    },
    {
      "Sid": "SecretsAccess",
      "Effect": "Allow",
      "Action": "secretsmanager:GetSecretValue",
      "Resource": "arn:aws:secretsmanager:ap-southeast-1:${ACCOUNT_ID}:secret:video-ad-auto/openai-*"
    }
  ]
}
```

---

### TTS Lambda (`lambda_tts`)

Generates audio voiceover using ElevenLabs (primary) or AWS Polly (fallback).

#### Required Permissions

| Service | Actions | Resource Scope |
|---------|---------|----------------|
| DynamoDB | `UpdateItem` | Projects table ARN |
| S3 | `PutObject` | Assets bucket ARN/* |
| Secrets Manager | `GetSecretValue` | ElevenLabs API key secret ARN |
| Polly | `SynthesizeSpeech` | All (service limitation) |

#### Recommended Policy

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DynamoDBAccess",
      "Effect": "Allow",
      "Action": "dynamodb:UpdateItem",
      "Resource": "arn:aws:dynamodb:ap-southeast-1:${ACCOUNT_ID}:table/${PROJECTS_TABLE}"
    },
    {
      "Sid": "S3Access",
      "Effect": "Allow",
      "Action": "s3:PutObject",
      "Resource": "arn:aws:s3:::${ASSETS_BUCKET}/*"
    },
    {
      "Sid": "SecretsAccess",
      "Effect": "Allow",
      "Action": "secretsmanager:GetSecretValue",
      "Resource": "arn:aws:secretsmanager:ap-southeast-1:${ACCOUNT_ID}:secret:video-ad-auto/elevenlabs-*"
    },
    {
      "Sid": "PollyAccess",
      "Effect": "Allow",
      "Action": "polly:SynthesizeSpeech",
      "Resource": "*"
    }
  ]
}
```

**Note:** AWS Polly does not support resource-level permissions for `SynthesizeSpeech`. The wildcard is required by AWS.

---

### Video Lambda (`lambda_video`)

Generates video using Kling AI API and stores results in S3.

#### Required Permissions

| Service | Actions | Resource Scope |
|---------|---------|----------------|
| DynamoDB | `UpdateItem` | Projects table ARN |
| S3 | `GetObject`, `PutObject` | Assets bucket ARN/* |
| Secrets Manager | `GetSecretValue` | Kling API key secret ARN |

#### Recommended Policy

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DynamoDBAccess",
      "Effect": "Allow",
      "Action": "dynamodb:UpdateItem",
      "Resource": "arn:aws:dynamodb:ap-southeast-1:${ACCOUNT_ID}:table/${PROJECTS_TABLE}"
    },
    {
      "Sid": "S3Access",
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:PutObject"
      ],
      "Resource": "arn:aws:s3:::${ASSETS_BUCKET}/*"
    },
    {
      "Sid": "SecretsAccess",
      "Effect": "Allow",
      "Action": "secretsmanager:GetSecretValue",
      "Resource": "arn:aws:secretsmanager:ap-southeast-1:${ACCOUNT_ID}:secret:video-ad-auto/kling-*"
    }
  ]
}
```

---

## Step Functions Execution Role

**Resource:** `aws_iam_role.state_machine_role`
**File:** `infra/modules/stepfunctions/main.tf`

### Current Permissions

| Service | Actions | Resource | Status |
|---------|---------|----------|--------|
| Lambda | `InvokeFunction` | Specific Lambda ARNs | Properly scoped |
| CloudWatch Logs | Log delivery management | `*` | Overly permissive |
| X-Ray | Tracing operations | `*` | Overly permissive |

### Recommended Changes

#### CloudWatch Logs - Scope to Log Group

```json
{
  "Effect": "Allow",
  "Action": [
    "logs:CreateLogDelivery",
    "logs:GetLogDelivery",
    "logs:UpdateLogDelivery",
    "logs:DeleteLogDelivery",
    "logs:ListLogDeliveries",
    "logs:PutResourcePolicy",
    "logs:DescribeResourcePolicies",
    "logs:DescribeLogGroups"
  ],
  "Resource": [
    "arn:aws:logs:ap-southeast-1:${ACCOUNT_ID}:log-group:/aws/vendedlogs/states/*",
    "arn:aws:logs:ap-southeast-1:${ACCOUNT_ID}:log-group:/aws/stepfunctions/*"
  ]
}
```

**Note:** Some CloudWatch Logs actions (like `DescribeLogGroups`) require `*` resource. Consider splitting into separate statements with appropriate resource scoping.

---

## Security Recommendations

### Critical - Implement Immediately

#### 1. Separate Lambda Roles per Function

**Risk:** Shared role violates least-privilege; compromised function gains access to all resources.

**Current State:**
```
lambda_api    ─┐
lambda_agents ─┼─> lambda_role (shared)
lambda_tts    ─┤
lambda_video  ─┘
```

**Recommended State:**
```
lambda_api    ──> api_lambda_role
lambda_agents ──> agents_lambda_role
lambda_tts    ──> tts_lambda_role
lambda_video  ──> video_lambda_role
```

**Implementation:** Update `infra/modules/lambda/` to create per-function roles or create four separate role resources.

#### 2. Wire Module Variables in main.tf

**Risk:** Lambda functions cannot access required AWS resources.

**Action:** Update `infra/main.tf` to pass required variables to Lambda module:

```hcl
module "lambda" {
  source = "./modules/lambda"

  # Add these variables
  dynamodb_table_arns = [module.dynamodb.table_arn]
  s3_bucket_arns      = [module.s3.bucket_arn]
  secrets_arns        = [
    module.secrets.openai_secret_arn,
    module.secrets.elevenlabs_secret_arn,
    module.secrets.kling_secret_arn
  ]
  sfn_arns            = [module.stepfunctions.state_machine_arn]
  polly_access        = true
}
```

### Medium Priority

#### 3. Scope Secret Access per Function

**Risk:** Each Lambda can access all secrets instead of only required ones.

**Recommendation:** Create separate secret ARN variables per function:
- API Lambda: OpenAI secret only
- Agent Lambda: OpenAI secret only
- TTS Lambda: ElevenLabs secret only
- Video Lambda: Kling secret only

#### 4. Add Resource Tags for Audit Trail

**Recommendation:** Add consistent tags to all IAM resources:

```hcl
tags = {
  Project     = "video-ad-auto"
  Environment = var.environment
  ManagedBy   = "terraform"
  SecurityAudit = "required"
}
```

### Low Priority

#### 5. Enable IAM Access Analyzer

**Recommendation:** Add IAM Access Analyzer to detect overly permissive policies:

```hcl
resource "aws_accessanalyzer_analyzer" "main" {
  analyzer_name = "video-ad-auto-analyzer"
  type          = "ACCOUNT"
}
```

#### 6. Implement Permission Boundaries

**Recommendation:** Add permission boundaries to prevent privilege escalation:

```hcl
resource "aws_iam_policy" "lambda_boundary" {
  name = "lambda-permission-boundary"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:*",
          "s3:*",
          "secretsmanager:GetSecretValue",
          "polly:SynthesizeSpeech",
          "states:StartExecution",
          "logs:*",
          "xray:*"
        ]
        Resource = "*"
        Condition = {
          StringEquals = {
            "aws:ResourceTag/Project" = "video-ad-auto"
          }
        }
      }
    ]
  })
}
```

---

## Compliance Checklist

| Requirement | Status | Notes |
|-------------|--------|-------|
| No `*` in resource ARNs (where avoidable) | Partial | Polly requires `*`, others should be scoped |
| Least privilege per function | Not Met | Single shared role |
| Secrets scoped per function | Not Met | All secrets accessible to all functions |
| DynamoDB scoped to specific tables | Supported | Module supports, not wired |
| S3 scoped to specific buckets | Supported | Module supports, not wired |
| IAM roles tagged | Not Met | No tags on IAM resources |
| Permission boundaries | Not Met | Not implemented |
| Access Analyzer enabled | Not Met | Not configured |

---

## Terraform Changes Required

### File: `infra/modules/lambda/iam.tf`

1. Create separate IAM roles for each Lambda function
2. Add tags to all IAM resources
3. Optional: Add permission boundary attachment

### File: `infra/main.tf`

1. Pass `dynamodb_table_arns` to Lambda module
2. Pass `s3_bucket_arns` to Lambda module
3. Pass `secrets_arns` to Lambda module (per-function)
4. Pass `sfn_arns` to Lambda module (API only)
5. Pass `polly_access = true` to Lambda module (TTS only)

### File: `infra/modules/stepfunctions/main.tf`

1. Scope CloudWatch Logs resource to specific log group patterns
2. Add tags to IAM role and policy

---

## Appendix: Current Policy Files

| File | Purpose |
|------|---------|
| `infra/modules/lambda/iam.tf` | Lambda IAM role and basic policy attachments |
| `infra/modules/lambda/policies.tf` | Conditional policies for AWS services |
| `infra/modules/stepfunctions/main.tf` | Step Functions role and inline policy |
| `infra/modules/cloudfront/main.tf` | S3 bucket policy for CloudFront OAI |
| `infra/modules/api_gateway/main.tf` | Lambda invoke permission for API Gateway |

---

## Revision History

| Date | Version | Author | Changes |
|------|---------|--------|---------|
| 2026-01-12 | 1.0 | Security Audit | Initial audit |
