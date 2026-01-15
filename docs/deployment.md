# Deployment Guide - AI Video Automation System

This document provides step-by-step instructions for deploying the AI Video Platform to AWS.

---

## Prerequisites

### Required Tools

| Tool | Version | Purpose |
|------|---------|---------|
| **Node.js** | 18+ | Frontend build |
| **Python** | 3.13+ | Backend development |
| **AWS CLI** | 2.x | AWS resource management |
| **Terraform** | 1.5+ | Infrastructure provisioning |
| **Docker** | 24+ | (Optional) Local testing |

### AWS Account Setup

1. **Create AWS Account** (if needed)
2. **Configure IAM User** with programmatic access:
   ```bash
   aws configure
   # Enter: Access Key ID, Secret Access Key, Region (ap-southeast-1)
   ```

3. **Required IAM Permissions:**
   - Lambda (Full Access)
   - API Gateway (Full Access)
   - DynamoDB (Full Access)
   - S3 (Full Access)
   - Cognito (Full Access)
   - Step Functions (Full Access)
   - CloudWatch (Full Access)
   - IAM (Limited - for Lambda roles)
   - Secrets Manager (Full Access)

### External API Keys

Obtain API keys from:

| Service | URL | Purpose |
|---------|-----|---------|
| **OpenAI** | https://platform.openai.com | GPT-4o for content generation |
| **ElevenLabs** | https://elevenlabs.io | Text-to-speech |
| **Kling AI** | https://klingai.com | Video generation |

---

## Environment Setup

### 1. Clone Repository

```bash
git clone https://github.com/your-org/video-ad-auto.git
cd video-ad-auto
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Copy environment template
cp .env.example .env
```

Edit `.env` with your configuration:
```env
ENVIRONMENT=dev
DEBUG=true
AWS_REGION=ap-southeast-1
COGNITO_USER_POOL_ID=your-pool-id
COGNITO_CLIENT_ID=your-client-id
DYNAMODB_USERS_TABLE=ai-video-users
DYNAMODB_PRODUCTS_TABLE=ai-video-products
DYNAMODB_JOBS_TABLE=ai-video-jobs
S3_IMAGES_BUCKET=ai-video-images-dev
S3_VIDEOS_BUCKET=ai-video-videos-dev
STEPFUNCTIONS_STATE_MACHINE_ARN=arn:aws:states:...
OPENAI_API_KEY=sk-...
ELEVENLABS_API_KEY=...
KLING_API_KEY=...
```

### 3. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Copy environment template
cp .env.example .env
```

Edit `.env`:
```env
VITE_API_URL=https://api.your-domain.com
VITE_COGNITO_USER_POOL_ID=your-pool-id
VITE_COGNITO_CLIENT_ID=your-client-id
VITE_COGNITO_REGION=ap-southeast-1
```

---

## Terraform Deployment

### 1. Initialize Terraform

```bash
cd infra

# Initialize providers and modules
terraform init
```

### 2. Create Variables File

Create `terraform.tfvars`:
```hcl
# General
name_prefix         = "ai-video"
environment         = "prod"
aws_region          = "ap-southeast-1"

# Cognito
cognito_callback_urls = ["https://your-domain.com/callback"]
cognito_logout_urls   = ["https://your-domain.com/logout"]

# Notifications
notification_email = "alerts@your-domain.com"
budget_limit       = "300"

# API Keys (store in Secrets Manager instead for production)
openai_api_key     = "sk-..."
elevenlabs_api_key = "..."
kling_api_key      = "..."
```

### 3. Plan Deployment

```bash
# Review what will be created
terraform plan -out=tfplan
```

### 4. Apply Infrastructure

```bash
# Create all resources
terraform apply tfplan
```

### 5. Note Outputs

After successful deployment, note the outputs:
```bash
terraform output

# Example outputs:
# api_gateway_url = "https://abc123.execute-api.ap-southeast-1.amazonaws.com/prod"
# cognito_user_pool_id = "ap-southeast-1_AbC123"
# cognito_client_id = "1abc2def3ghi..."
# s3_images_bucket = "ai-video-images-prod-xyz"
# s3_videos_bucket = "ai-video-videos-prod-xyz"
```

---

## Lambda Deployment

### Build and Package

```bash
cd backend

# Create deployment package
pip install -r requirements.txt -t package/
cp -r src package/
cd package && zip -r ../deployment.zip . && cd ..

# Upload to S3
aws s3 cp deployment.zip s3://ai-video-deployments/api/deployment.zip
```

### Update Lambda Functions

```bash
# Update API Lambda
aws lambda update-function-code \
  --function-name ai-video-api \
  --s3-bucket ai-video-deployments \
  --s3-key api/deployment.zip \
  --region ap-southeast-1

# Repeat for other Lambdas (agent, tts, video)
```

---

## Frontend Deployment

### Build for Production

```bash
cd frontend

# Build optimized bundle
npm run build
```

### Deploy to S3

```bash
# Sync build output to S3
aws s3 sync dist/ s3://ai-video-webapp-prod/ --delete

# Invalidate CloudFront cache (if using)
aws cloudfront create-invalidation \
  --distribution-id YOUR_DIST_ID \
  --paths "/*"
```

---

## Post-Deployment Verification

### 1. Health Check

```bash
# Check API health
curl https://api.your-domain.com/health

# Expected response:
# {"status": "healthy", "environment": "prod"}
```

### 2. Authentication Test

```bash
# Test user registration
curl -X POST https://api.your-domain.com/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "SecurePass123!"}'
```

### 3. Lambda Function Tests

```bash
# Check Lambda invocations
aws logs tail /aws/lambda/ai-video-api --follow --region ap-southeast-1
```

### 4. DynamoDB Tables

```bash
# Verify tables exist
aws dynamodb list-tables --region ap-southeast-1

# Check table status
aws dynamodb describe-table --table-name ai-video-users --region ap-southeast-1
```

### 5. Step Functions

```bash
# List state machines
aws stepfunctions list-state-machines --region ap-southeast-1

# Check recent executions
aws stepfunctions list-executions \
  --state-machine-arn arn:aws:states:ap-southeast-1:ACCOUNT:stateMachine:video-pipeline \
  --max-results 5 \
  --region ap-southeast-1
```

---

## CI/CD Pipeline

### GitHub Actions Workflow

The repository includes GitHub Actions workflows for:

| Workflow | Trigger | Actions |
|----------|---------|---------|
| `test.yml` | Push/PR | Run all tests |
| `deploy-dev.yml` | Push to `develop` | Deploy to dev environment |
| `deploy-prod.yml` | Push to `main` | Deploy to production |

### Required Secrets

Configure in GitHub repository settings:

```
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
AWS_REGION
OPENAI_API_KEY
ELEVENLABS_API_KEY
KLING_API_KEY
```

---

## Environment-Specific Configuration

### Development

```hcl
environment        = "dev"
budget_limit       = "50"
log_retention_days = 7
```

### Staging

```hcl
environment        = "staging"
budget_limit       = "100"
log_retention_days = 14
```

### Production

```hcl
environment        = "prod"
budget_limit       = "300"
log_retention_days = 90
```

---

## Rollback Procedures

### Lambda Rollback

```bash
# List Lambda versions
aws lambda list-versions-by-function \
  --function-name ai-video-api \
  --region ap-southeast-1

# Update alias to previous version
aws lambda update-alias \
  --function-name ai-video-api \
  --name prod \
  --function-version PREVIOUS_VERSION \
  --region ap-southeast-1
```

### Terraform Rollback

```bash
# View state history (if using remote backend with versioning)
terraform state list

# Revert to previous state
terraform apply -target=module.api_lambda -var="function_version=previous"
```

---

## Troubleshooting Deployment

| Issue | Solution |
|-------|----------|
| Terraform init fails | Check AWS credentials: `aws sts get-caller-identity` |
| Lambda deployment fails | Verify S3 bucket exists and has correct permissions |
| API Gateway 5xx | Check Lambda logs: `aws logs tail /aws/lambda/...` |
| Cognito auth fails | Verify callback URLs match exactly |
| DynamoDB throttling | Consider switching to provisioned capacity |

---

## Related Documents

- [Architecture Overview](/docs/architecture.md)
- [API Reference](/docs/api-reference.md)
- [Troubleshooting Guide](/docs/troubleshooting.md)
- [Secrets Rotation](/docs/runbook/secrets-rotation.md)
