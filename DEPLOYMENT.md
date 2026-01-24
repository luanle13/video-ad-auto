# AWS Deployment Guide - AI Video Automation Platform

First-time manual deployment to development environment.

---

## Prerequisites Checklist

Before starting, ensure you have:

- AWS Account
- Node.js 18+ installed
- Python 3.13+ installed
- Terraform 1.5+ installed
- Docker installed (for Lambda container deployment)
- External API keys (see below)

### Required API Keys

| Service | Sign Up URL | Purpose | Pricing |
|---------|-------------|---------|---------|
| OpenAI | https://platform.openai.com/signup | GPT-4o for script generation | Pay-per-use (~$0.01/1K tokens) |
| ElevenLabs | https://elevenlabs.io/sign-up | Text-to-speech | Free tier: 10K chars/month |
| DeepInfra | https://deepinfra.com/dash/api_keys | Veo 3.1 Fast video generation | Pay-per-use (~$0.50/video) |

> **Note:** You can deploy infrastructure first and add API keys later to Secrets Manager (Step 4). The system will show errors for missing keys but won't break.

---

## Step 1: Configure AWS CLI

### Install AWS CLI (if not installed)

```bash
# macOS
brew install awscli
```

### Configure credentials

```bash
aws configure
# Enter:
#   Access Key ID: <from IAM console>
#   Secret Access Key: <from IAM console>
#   Region: ap-southeast-1
#   Output format: json

# Verify setup
aws sts get-caller-identity
```

### Getting AWS Credentials

1. Go to AWS Console → IAM → Users → Create user
2. Attach the required policies (listed below)
3. Create access key

### Required IAM Policies

- `AmazonDynamoDBFullAccess`
- `AmazonS3FullAccess`
- `AWSLambda_FullAccess`
- `AmazonAPIGatewayAdministrator`
- `AmazonCognitoPowerUser`
- `AWSStepFunctionsFullAccess`
- `SecretsManagerReadWrite`
- `CloudWatchFullAccess`
- `IAMFullAccess` (for creating Lambda roles)
- `AmazonEC2ContainerRegistryFullAccess` (for ECR container images)

---

## Step 2: Create Terraform State Bucket

```bash
# Create S3 bucket for Terraform state (one-time setup)
# Replace YOUR-ACCOUNT-ID with your actual AWS account ID
aws s3 mb s3://ai-video-terraform-state-YOUR-ACCOUNT-ID --region ap-southeast-1

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket ai-video-terraform-state-YOUR-ACCOUNT-ID \
  --versioning-configuration Status=Enabled
```

---

## Step 3: Deploy Infrastructure with Terraform

```bash
cd infra

# Initialize Terraform (replace YOUR-ACCOUNT-ID)
terraform init \
  -backend-config="bucket=ai-video-terraform-state-YOUR-ACCOUNT-ID" \
  -backend-config="key=dev/terraform.tfstate" \
  -backend-config="region=ap-southeast-1"

# Review deployment plan
terraform plan -var-file=environments/dev.tfvars -out=tfplan

# Apply infrastructure (creates ~40 AWS resources)
terraform apply tfplan

# Save outputs for next steps
terraform output > ../outputs.txt
terraform output -json > ../outputs.json
```

### Resources Created

- 3 DynamoDB tables (users, products, jobs)
- 4 S3 buckets (images, videos, webapp, deployments)
- 1 ECR repository (for Lambda container images)
- 4 Lambda functions (api, agents, tts, video)
- API Gateway REST API
- Cognito User Pool
- Step Functions state machine
- CloudWatch dashboards & alarms
- Secrets Manager secrets

---

## Step 4: Store API Keys in Secrets Manager

```bash
# Store OpenAI key
aws secretsmanager put-secret-value \
  --secret-id ai-video-dev/openai-api-key \
  --secret-string '{"api_key":"YOUR_OPENAI_API_KEY"}' \
  --region ap-southeast-1

# Store ElevenLabs key
aws secretsmanager put-secret-value \
  --secret-id ai-video-dev/elevenlabs-api-key \
  --secret-string '{"api_key":"YOUR_ELEVENLABS_API_KEY"}' \
  --region ap-southeast-1

# Store DeepInfra key (for Veo 3.1 video generation)
aws secretsmanager put-secret-value \
  --secret-id ai-video-dev/deepinfra-api-key \
  --secret-string '{"api_key":"YOUR_DEEPINFRA_API_KEY"}' \
  --region ap-southeast-1
```

---

## Step 5: Deploy Backend (Lambda Container Images)

The backend uses container-based Lambda deployment to handle large AI dependencies (crewai, chromadb, etc.) that exceed the 250MB zip limit. All Lambda functions share a single container image, with the handler specified via Terraform.

```bash
cd backend

# Get ECR repository URL from Terraform outputs
ECR_REPO=$(cd ../infra && terraform output -raw ecr_repository_url)
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=ap-southeast-1

# Login to ECR
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# Build the container image (flags prevent multi-arch manifest issues with Lambda)
docker build --platform linux/arm64 --provenance=false --sbom=false -t $ECR_REPO:latest .

# Push to ECR
docker push $ECR_REPO:latest

# Update all Lambda functions to use the new image
for func in api agents tts video; do
  aws lambda update-function-code \
    --function-name ai-video-dev-$func-handler \
    --image-uri $ECR_REPO:latest \
    --region $AWS_REGION
  echo "Updated $func Lambda"
done
```

### First-time Deployment Note

On first deployment, you need to push an image to ECR **before** running `terraform apply` since Lambdas reference the image. Use this sequence:

```bash
# 1. First, apply only ECR repository
cd infra
terraform apply -target=aws_ecr_repository.lambda -target=aws_ecr_lifecycle_policy.lambda -var-file=environments/dev.tfvars

# 2. Build and push image to ECR
cd ../backend
ECR_REPO=$(cd ../infra && terraform output -raw ecr_repository_url)
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=ap-southeast-1

aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com
docker build --platform linux/arm64 --provenance=false --sbom=false -t $ECR_REPO:latest .
docker push $ECR_REPO:latest

# 3. Then apply the rest of the infrastructure
cd ../infra
terraform apply -var-file=environments/dev.tfvars
```

---

## Step 6: Deploy Frontend

```bash
cd frontend

# Install dependencies
npm install

# Get values from Terraform outputs
cd ../infra
API_URL=$(terraform output -raw api_endpoint)
COGNITO_POOL_ID=$(terraform output -raw cognito_user_pool_id)
COGNITO_CLIENT_ID=$(terraform output -raw cognito_app_client_id)
WEBAPP_BUCKET=$(terraform output -raw s3_webapp_bucket)
cd ../frontend

# Create .env.production file (used by Vite for production builds)
# Note: .env.production takes precedence over .env.local during 'npm run build'
cat > .env.production << EOF
VITE_API_URL=${API_URL}dev
VITE_COGNITO_USER_POOL_ID=$COGNITO_POOL_ID
VITE_COGNITO_CLIENT_ID=$COGNITO_CLIENT_ID
VITE_COGNITO_REGION=ap-southeast-1
EOF

# Verify the .env.production file
echo "Production environment:"
cat .env.production

# Build for production
npm run build

# Verify the API URL is correct in the build
grep -o 'https://[^"]*execute-api[^"]*' dist/assets/*.js | head -1

# Deploy to S3
aws s3 sync dist/ s3://$WEBAPP_BUCKET --delete

# Get CloudFront distribution ID and invalidate cache
DIST_ID=$(cd ../infra && terraform output -raw cloudfront_distribution_id)
aws cloudfront create-invalidation --distribution-id $DIST_ID --paths "/*"
```

> **Important:**
> - The API Gateway endpoint from Terraform ends with `/`. The stage name `dev` must be appended to form the complete API URL (e.g., `https://xxx.execute-api.ap-southeast-1.amazonaws.com/dev`).
> - Use `.env.production` for production builds, NOT `.env`. Vite's priority order: `.env` < `.env.local` < `.env.production`. Using `.env.production` ensures production values are used even if `.env.local` exists for local development.

---

## Step 7: Verify Deployment

```bash
cd infra

# Get API URL (append stage name 'dev')
API_URL="$(terraform output -raw api_endpoint)dev"

# Test health endpoint
curl $API_URL/health
# Expected: {"status": "healthy", "version": "0.1.0", "timestamp": "..."}

# Check Lambda logs
aws logs tail /aws/lambda/ai-video-dev-api-handler --follow --region ap-southeast-1

# Verify DynamoDB tables
aws dynamodb list-tables --region ap-southeast-1

# Check Step Functions
aws stepfunctions list-state-machines --region ap-southeast-1

# Get frontend URL
FRONTEND_URL=$(terraform output -raw cloudfront_domain_name)
echo "Frontend: https://$FRONTEND_URL"

# Display all important URLs
echo ""
echo "=== Deployment URLs ==="
echo "API:      $API_URL"
echo "Frontend: https://$FRONTEND_URL"
echo "======================="
```

---

## Step 8: Test End-to-End

1. Open the CloudFront URL in browser
2. Register a new user account
3. Create a product with an image
4. Generate a video for the product
5. Check job status and download video

---

## Estimated AWS Costs (Dev Environment)

| Service | Monthly Estimate |
|---------|------------------|
| Lambda | ~$5-15 (depends on usage) |
| DynamoDB | ~$1 (on-demand) |
| S3 | ~$1-5 (depends on storage) |
| API Gateway | ~$3-10 |
| CloudFront | ~$1-5 |
| Cognito | Free (under 50k MAU) |
| **Total** | **~$15-40/month** |

> Budget alert configured at $50 (from dev.tfvars).

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `terraform init` fails | Check AWS credentials: `aws sts get-caller-identity` |
| Lambda timeout | Check CloudWatch logs for errors |
| API 5xx errors | Verify Lambda has correct IAM permissions |
| Cognito auth fails | Check callback URLs in Cognito settings |
| Video generation fails | Verify API keys in Secrets Manager |
| Deployment package too large | Remove unnecessary dependencies or use container-based Lambda |
| Lambda update fails with "image manifest not supported" | Add `--provenance=false --sbom=false` flags to docker build |
| Frontend shows localhost API errors | Ensure `.env` has correct API URL with stage name (e.g., `.../dev`) |
| Health endpoint returns 404 | Use correct path: `${API_URL}dev/health` (include stage name) |
| CloudFront shows old content | Wait 1-2 min for cache invalidation or check invalidation status |

---

## Files Modified/Created

- `infra/` - Terraform applies infrastructure
- `backend/deployment.zip` - Lambda deployment package
- `frontend/.env` - Frontend environment variables
- `frontend/dist/` - Built frontend assets

---

## Next Steps After Deployment

1. **Custom Domain:** Configure Route 53 + ACM certificate for custom domain
2. **CI/CD:** Set up GitHub Actions for automated deployments (see below)
3. **Monitoring:** Review CloudWatch dashboards at AWS Console
4. **Production:** When ready, deploy to prod using `environments/prod.tfvars`

---

## CI/CD with GitHub Actions

The project includes pre-configured GitHub Actions workflows for automated deployments.

### Workflows Overview

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `ci.yml` | Push to any branch, PRs | Lint, test, security scan, validate |
| `deploy-dev.yml` | Push to `develop` branch | Deploy to development environment |
| `deploy-prod.yml` | Push to `main` branch | Deploy to production environment |

### CI Pipeline Checks

The CI pipeline runs these checks (all must pass before deployment):

1. **backend-lint** - Ruff linting + mypy type checking
2. **backend-test** - pytest with 80% coverage requirement
3. **backend-security** - Trivy vulnerability scanner
4. **frontend-lint** - ESLint + TypeScript type checking
5. **frontend-test** - Vitest with coverage
6. **frontend-build** - Build and verify artifacts
7. **terraform-validate** - Format check + Terraform validate

### Setting Up GitHub Actions OIDC

GitHub Actions uses OIDC to authenticate with AWS without long-lived credentials.

#### Step 1: Create OIDC Identity Provider in AWS

```bash
# Create the OIDC provider (one-time setup)
aws iam create-open-id-connect-provider \
  --url https://token.actions.githubusercontent.com \
  --client-id-list sts.amazonaws.com \
  --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1 \
  --region ap-southeast-1
```

#### Step 2: Create GitHub Actions IAM Role

Create a file `github-actions-role.json`:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::YOUR_ACCOUNT_ID:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:YOUR_GITHUB_ORG/video-ad-auto:*"
        }
      }
    }
  ]
}
```

Create the role:

```bash
# Replace YOUR_ACCOUNT_ID and YOUR_GITHUB_ORG in the JSON file first

aws iam create-role \
  --role-name GitHubActionsRole \
  --assume-role-policy-document file://github-actions-role.json

# Attach required policies
aws iam attach-role-policy --role-name GitHubActionsRole --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess
aws iam attach-role-policy --role-name GitHubActionsRole --policy-arn arn:aws:iam::aws:policy/AWSLambda_FullAccess
aws iam attach-role-policy --role-name GitHubActionsRole --policy-arn arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryFullAccess
aws iam attach-role-policy --role-name GitHubActionsRole --policy-arn arn:aws:iam::aws:policy/CloudFrontFullAccess
aws iam attach-role-policy --role-name GitHubActionsRole --policy-arn arn:aws:iam::aws:policy/IAMFullAccess
aws iam attach-role-policy --role-name GitHubActionsRole --policy-arn arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess
aws iam attach-role-policy --role-name GitHubActionsRole --policy-arn arn:aws:iam::aws:policy/AmazonAPIGatewayAdministrator
aws iam attach-role-policy --role-name GitHubActionsRole --policy-arn arn:aws:iam::aws:policy/AmazonCognitoPowerUser
aws iam attach-role-policy --role-name GitHubActionsRole --policy-arn arn:aws:iam::aws:policy/AWSStepFunctionsFullAccess
aws iam attach-role-policy --role-name GitHubActionsRole --policy-arn arn:aws:iam::aws:policy/SecretsManagerReadWrite
aws iam attach-role-policy --role-name GitHubActionsRole --policy-arn arn:aws:iam::aws:policy/CloudWatchFullAccess
```

#### Step 3: Configure GitHub Secrets

Go to your GitHub repository → Settings → Secrets and variables → Actions.

Add these **Repository Secrets**:

| Secret Name | Value | Description |
|-------------|-------|-------------|
| `AWS_ACCOUNT_ID` | `123456789012` | Your AWS account ID |
| `TERRAFORM_STATE_BUCKET` | `ai-video-terraform-state-YOUR-ACCOUNT-ID` | Terraform state bucket name |
| `ARTIFACTS_BUCKET` | `ai-video-dev-deployment` | S3 bucket for Lambda packages |
| `WEBAPP_BUCKET` | `ai-video-dev-webapp` | S3 bucket for frontend assets |
| `CLOUDFRONT_DISTRIBUTION_ID` | `E1234567890ABC` | CloudFront distribution ID |
| `SLACK_WEBHOOK` | `https://hooks.slack.com/...` | (Optional) For prod notifications |

Get the values from Terraform outputs:

```bash
cd infra
terraform output deployment_bucket        # → ARTIFACTS_BUCKET
terraform output s3_webapp_bucket          # → WEBAPP_BUCKET
terraform output cloudfront_distribution_id # → CLOUDFRONT_DISTRIBUTION_ID
```

#### Step 4: Configure GitHub Environments

Go to your GitHub repository → Settings → Environments.

Create two environments:

1. **development**
   - No protection rules (auto-deploy)

2. **production**
   - Add required reviewers (recommended)
   - Add environment secret `SLACK_WEBHOOK` if using Slack notifications

### Automated Deployment Flow

```
Push to develop branch
       ↓
   CI Pipeline
   (lint, test, security)
       ↓
   [All checks pass]
       ↓
   Deploy to Dev
   (backend, infra, frontend)


Push to main branch
       ↓
   CI Pipeline
       ↓
   [All checks pass]
       ↓
   [Manual approval - optional]
       ↓
   Deploy to Prod
```

### Manual Deployment Trigger

You can also trigger deployments manually:

1. Go to Actions → Deploy Dev (or Deploy Prod)
2. Click "Run workflow"
3. Select the branch and click "Run workflow"

---

## Subsequent Deployments (Code Updates)

After the initial deployment, use these simplified steps to deploy code changes.

### Backend Changes Only

```bash
cd backend

# Get ECR repository URL and set variables
ECR_REPO=$(cd ../infra && terraform output -raw ecr_repository_url)
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION="ap-southeast-1"

# Login to ECR
aws ecr get-login-password --region $AWS_REGION | \
  docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# Build and push new image (flags prevent multi-arch manifest issues)
docker build --platform linux/arm64 --provenance=false --sbom=false -t $ECR_REPO:latest .
docker push $ECR_REPO:latest

# Update Lambda functions to use new image
for func in api agents tts video; do
  echo "Updating ai-video-dev-$func-handler..."
  aws lambda update-function-code \
    --function-name ai-video-dev-$func-handler \
    --image-uri $ECR_REPO:latest \
    --region $AWS_REGION \
    --query 'FunctionName' --output text
done

# Verify deployment
API_URL="$(cd ../infra && terraform output -raw api_endpoint)dev"
echo ""
echo "Testing health endpoint..."
curl -s $API_URL/health
```

### Frontend Changes Only

```bash
cd frontend

# Ensure .env.production has correct API URL (only needed if missing)
if [ ! -f .env.production ]; then
  cd ../infra
  API_URL=$(terraform output -raw api_endpoint)
  COGNITO_POOL_ID=$(terraform output -raw cognito_user_pool_id)
  COGNITO_CLIENT_ID=$(terraform output -raw cognito_app_client_id)
  cd ../frontend
  cat > .env.production << EOF
VITE_API_URL=${API_URL}dev
VITE_COGNITO_USER_POOL_ID=$COGNITO_POOL_ID
VITE_COGNITO_CLIENT_ID=$COGNITO_CLIENT_ID
VITE_COGNITO_REGION=ap-southeast-1
EOF
  echo "Created .env.production"
fi

# Build
npm run build

# Verify correct API URL in build
echo "API URL in build:"
grep -o 'https://[^"]*execute-api[^"]*' dist/assets/*.js | head -1

# Deploy to S3
WEBAPP_BUCKET=$(cd ../infra && terraform output -raw s3_webapp_bucket)
aws s3 sync dist/ s3://$WEBAPP_BUCKET --delete

# Invalidate CloudFront cache
DIST_ID=$(cd ../infra && terraform output -raw cloudfront_distribution_id)
aws cloudfront create-invalidation --distribution-id $DIST_ID --paths "/*"

# Display frontend URL
FRONTEND_URL=$(cd ../infra && terraform output -raw cloudfront_domain_name)
echo ""
echo "Frontend deployed: https://$FRONTEND_URL"
echo "Cache invalidation in progress (1-2 minutes)"
```

### Full Stack Deployment (Backend + Frontend)

```bash
# Deploy backend
cd backend
ECR_REPO=$(cd ../infra && terraform output -raw ecr_repository_url)
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION="ap-southeast-1"

aws ecr get-login-password --region $AWS_REGION | \
  docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com
docker build --platform linux/arm64 --provenance=false --sbom=false -t $ECR_REPO:latest .
docker push $ECR_REPO:latest

for func in api agents tts video; do
  aws lambda update-function-code \
    --function-name ai-video-dev-$func-handler \
    --image-uri $ECR_REPO:latest \
    --region $AWS_REGION \
    --query 'FunctionName' --output text
done

# Deploy frontend
cd ../frontend
npm run build
WEBAPP_BUCKET=$(cd ../infra && terraform output -raw s3_webapp_bucket)
aws s3 sync dist/ s3://$WEBAPP_BUCKET --delete
DIST_ID=$(cd ../infra && terraform output -raw cloudfront_distribution_id)
aws cloudfront create-invalidation --distribution-id $DIST_ID --paths "/*"

# Verify
cd ../infra
API_URL="$(terraform output -raw api_endpoint)dev"
FRONTEND_URL=$(terraform output -raw cloudfront_domain_name)
echo ""
echo "=== Deployment Complete ==="
echo "API:      $API_URL"
echo "Frontend: https://$FRONTEND_URL"
curl -s $API_URL/health
```

### Infrastructure Changes

```bash
cd infra

# Review changes
terraform plan -var-file=environments/dev.tfvars

# Apply changes
terraform apply -var-file=environments/dev.tfvars
```

---

## Tear Down All Resources

To destroy all AWS resources and stop incurring charges:

### Step 1: Empty S3 Buckets

S3 buckets must be empty before Terraform can delete them.

```bash
cd infra

# Get bucket names
IMAGES_BUCKET=$(terraform output -raw s3_images_bucket)
VIDEOS_BUCKET=$(terraform output -raw s3_videos_bucket)
WEBAPP_BUCKET=$(terraform output -raw s3_webapp_bucket)
DEPLOY_BUCKET=$(terraform output -raw deployment_bucket)

echo "Emptying S3 buckets..."
aws s3 rm s3://$IMAGES_BUCKET --recursive
aws s3 rm s3://$VIDEOS_BUCKET --recursive
aws s3 rm s3://$WEBAPP_BUCKET --recursive
aws s3 rm s3://$DEPLOY_BUCKET --recursive
echo "All buckets emptied."
```

### Step 2: Delete ECR Images

```bash
# Get repository name
ECR_REPO_NAME="ai-video-dev-lambda"

# List images first
echo "Images in ECR repository:"
aws ecr list-images --repository-name $ECR_REPO_NAME --region ap-southeast-1

# Delete all images in the repository
aws ecr batch-delete-image \
  --repository-name $ECR_REPO_NAME \
  --image-ids "$(aws ecr list-images --repository-name $ECR_REPO_NAME --query 'imageIds[*]' --output json)" \
  --region ap-southeast-1 2>/dev/null || echo "No images to delete"

echo "ECR images deleted."
```

### Step 3: Destroy Infrastructure with Terraform

```bash
cd infra

# Review what will be destroyed
terraform plan -destroy -var-file=environments/dev.tfvars

# Destroy all resources (type 'yes' to confirm)
terraform destroy -var-file=environments/dev.tfvars
```

### Step 4: Delete CloudWatch Logs

CloudWatch Logs are retained by default even after Terraform destroy.

```bash
echo "Deleting CloudWatch log groups..."
for func in api agents tts video; do
  aws logs delete-log-group \
    --log-group-name /aws/lambda/ai-video-dev-$func-handler \
    --region ap-southeast-1 2>/dev/null && echo "Deleted /aws/lambda/ai-video-dev-$func-handler"
done

# Also delete Step Functions logs if exists
aws logs delete-log-group \
  --log-group-name /aws/states/ai-video-dev-video-pipeline \
  --region ap-southeast-1 2>/dev/null && echo "Deleted Step Functions logs"

echo "CloudWatch logs deleted."
```

### Step 5: (Optional) Delete GitHub Actions OIDC Resources

If you set up GitHub Actions OIDC, remove these resources:

```bash
# Detach policies from GitHubActionsRole
for policy in AmazonS3FullAccess AWSLambda_FullAccess AmazonEC2ContainerRegistryFullAccess \
  CloudFrontFullAccess IAMFullAccess AmazonDynamoDBFullAccess AmazonAPIGatewayAdministrator \
  AmazonCognitoPowerUser AWSStepFunctionsFullAccess SecretsManagerReadWrite CloudWatchFullAccess; do
  aws iam detach-role-policy \
    --role-name GitHubActionsRole \
    --policy-arn arn:aws:iam::aws:policy/$policy 2>/dev/null
done

# Delete the role
aws iam delete-role --role-name GitHubActionsRole 2>/dev/null && echo "Deleted GitHubActionsRole"

# Delete OIDC provider
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
aws iam delete-open-id-connect-provider \
  --open-id-connect-provider-arn arn:aws:iam::$AWS_ACCOUNT_ID:oidc-provider/token.actions.githubusercontent.com \
  2>/dev/null && echo "Deleted OIDC provider"
```

### Step 6: (Optional) Delete Terraform State Bucket

If you want to completely remove everything including the Terraform state:

```bash
# Get your account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Empty and delete the state bucket
aws s3 rm s3://ai-video-terraform-state-$AWS_ACCOUNT_ID --recursive
aws s3 rb s3://ai-video-terraform-state-$AWS_ACCOUNT_ID

echo "Terraform state bucket deleted."
```

> **Warning:** Deleting the state bucket means you lose all Terraform state. Only do this if you're completely done with the project.

### Step 7: Clean Up Local Files

```bash
# Remove local build artifacts
rm -rf backend/package backend/deployment.zip
rm -rf frontend/dist frontend/node_modules frontend/.env frontend/.env.production
rm -rf infra/.terraform infra/tfplan infra/.terraform.lock.hcl
rm -f outputs.txt outputs.json

echo "Local files cleaned up."
```

### Complete Tear Down Script

For convenience, here's a complete script that performs all tear down steps:

```bash
#!/bin/bash
set -e

echo "=== AI Video Platform - Complete Tear Down ==="
echo ""

cd infra

# Step 1: Empty S3 buckets
echo "Step 1: Emptying S3 buckets..."
for bucket in s3_images_bucket s3_videos_bucket s3_webapp_bucket deployment_bucket; do
  BUCKET_NAME=$(terraform output -raw $bucket 2>/dev/null) || continue
  echo "  Emptying $BUCKET_NAME..."
  aws s3 rm s3://$BUCKET_NAME --recursive 2>/dev/null || true
done

# Step 2: Delete ECR images
echo "Step 2: Deleting ECR images..."
ECR_REPO_NAME="ai-video-dev-lambda"
aws ecr batch-delete-image \
  --repository-name $ECR_REPO_NAME \
  --image-ids "$(aws ecr list-images --repository-name $ECR_REPO_NAME --query 'imageIds[*]' --output json 2>/dev/null)" \
  --region ap-southeast-1 2>/dev/null || true

# Step 3: Terraform destroy
echo "Step 3: Destroying infrastructure..."
terraform destroy -var-file=environments/dev.tfvars -auto-approve

# Step 4: Delete CloudWatch logs
echo "Step 4: Deleting CloudWatch logs..."
for func in api agents tts video; do
  aws logs delete-log-group \
    --log-group-name /aws/lambda/ai-video-dev-$func-handler \
    --region ap-southeast-1 2>/dev/null || true
done

# Step 5: Clean up local files
echo "Step 5: Cleaning up local files..."
cd ..
rm -rf backend/package backend/deployment.zip
rm -rf frontend/dist frontend/.env frontend/.env.production
rm -rf infra/.terraform infra/tfplan infra/.terraform.lock.hcl
rm -f outputs.txt outputs.json

echo ""
echo "=== Tear Down Complete ==="
echo "Note: Terraform state bucket and GitHub OIDC resources were NOT deleted."
echo "Delete them manually if you want to completely remove everything."
```

### Resources Destroyed

After running the tear down, the following will be deleted:

| Category | Resources |
|----------|-----------|
| **Compute** | 4 Lambda functions (api, agents, tts, video) |
| **Storage** | 4 S3 buckets, 1 ECR repository |
| **Database** | 3 DynamoDB tables (users, products, jobs) + all data |
| **API** | API Gateway REST API, CloudFront distribution |
| **Auth** | Cognito User Pool + all registered users |
| **Orchestration** | Step Functions state machine |
| **Monitoring** | CloudWatch dashboards, alarms, log groups |
| **Secrets** | 4 Secrets Manager secrets (API keys) |
| **IAM** | Lambda execution roles and policies |

### Resources NOT Automatically Deleted

These require manual deletion:

| Resource | Reason | Manual Command |
|----------|--------|----------------|
| Terraform state bucket | Contains infrastructure state | See Step 6 |
| GitHub OIDC provider | External integration | See Step 5 |
| GitHubActionsRole | External integration | See Step 5 |
| AWS Budgets alerts | May have email subscriptions | Delete via AWS Console |
