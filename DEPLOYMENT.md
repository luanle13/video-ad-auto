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
| Kling AI | https://klingai.com | Video generation | Subscription-based |

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
  --secret-id ai-video-dev-openai-key \
  --secret-string '{"api_key":"YOUR_OPENAI_API_KEY"}' \
  --region ap-southeast-1

# Store ElevenLabs key
aws secretsmanager put-secret-value \
  --secret-id ai-video-dev/elevenlabs-api-key \
  --secret-string '{"api_key":"YOUR_ELEVENLABS_API_KEY"}' \
  --region ap-southeast-1

# Store Kling AI keys
aws secretsmanager put-secret-value \
  --secret-id ai-video-dev/kling-api-key \
  --secret-string '{"access_key":"YOUR_ACCESS_KEY","secret_key":"YOUR_SECRET_KEY"}' \
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

# Build the container image
docker build --platform linux/arm64 -t $ECR_REPO:latest .

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
docker build --platform linux/arm64 -t $ECR_REPO:latest .
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

# Create .env file
cat > .env << EOF
VITE_API_URL=$API_URL
VITE_COGNITO_USER_POOL_ID=$COGNITO_POOL_ID
VITE_COGNITO_CLIENT_ID=$COGNITO_CLIENT_ID
VITE_COGNITO_REGION=ap-southeast-1
EOF

# Build for production
npm run build

# Deploy to S3
aws s3 sync dist/ s3://$WEBAPP_BUCKET --delete

# Get CloudFront distribution ID and invalidate cache
DIST_ID=$(cd ../infra && terraform output -raw cloudfront_distribution_id)
aws cloudfront create-invalidation --distribution-id $DIST_ID --paths "/*"
```

---

## Step 7: Verify Deployment

```bash
cd infra

# Get API URL
API_URL=$(terraform output -raw api_endpoint)

# Test health endpoint
curl $API_URL/health
# Expected: {"status": "healthy", "environment": "dev"}

# Check Lambda logs
aws logs tail /aws/lambda/ai-video-dev-api-handler --follow --region ap-southeast-1

# Verify DynamoDB tables
aws dynamodb list-tables --region ap-southeast-1

# Check Step Functions
aws stepfunctions list-state-machines --region ap-southeast-1

# Get frontend URL
FRONTEND_URL=$(terraform output -raw cloudfront_domain_name)
echo "Frontend: https://$FRONTEND_URL"
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

---

## Files Modified/Created

- `infra/` - Terraform applies infrastructure
- `backend/deployment.zip` - Lambda deployment package
- `frontend/.env` - Frontend environment variables
- `frontend/dist/` - Built frontend assets

---

## Next Steps After Deployment

1. **Custom Domain:** Configure Route 53 + ACM certificate for custom domain
2. **CI/CD:** Set up GitHub Actions for automated deployments (workflows already exist)
3. **Monitoring:** Review CloudWatch dashboards at AWS Console
4. **Production:** When ready, deploy to prod using `environments/prod.tfvars`

---

## Subsequent Deployments (Code Updates)

After the initial deployment, use these simplified steps to deploy code changes.

### Backend Changes Only

```bash
cd backend

# Set variables
export ECR_REPO="YOUR_AWS_ACCOUNT_ID.dkr.ecr.ap-southeast-1.amazonaws.com/ai-video-dev-lambda"
export AWS_REGION="ap-southeast-1"

# Login to ECR
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin YOUR_AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# Build and push new image
docker build --platform linux/arm64 -t $ECR_REPO:latest .
docker push $ECR_REPO:latest

# Update Lambda functions to use new image
for func in api agents tts video; do
  aws lambda update-function-code \
    --function-name ai-video-dev-$func-handler \
    --image-uri $ECR_REPO:latest \
    --region $AWS_REGION
  echo "Updated $func Lambda"
done
```

### Frontend Changes Only

```bash
cd frontend

# Build
npm run build

# Deploy to S3
WEBAPP_BUCKET=$(cd ../infra && terraform output -raw s3_webapp_bucket)
aws s3 sync dist/ s3://$WEBAPP_BUCKET --delete

# Invalidate CloudFront cache
DIST_ID=$(cd ../infra && terraform output -raw cloudfront_distribution_id)
aws cloudfront create-invalidation --distribution-id $DIST_ID --paths "/*"
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
# Get bucket names
cd infra
IMAGES_BUCKET=$(terraform output -raw s3_images_bucket)
VIDEOS_BUCKET=$(terraform output -raw s3_videos_bucket)
WEBAPP_BUCKET=$(terraform output -raw s3_webapp_bucket)
DEPLOY_BUCKET=$(terraform output -raw deployment_bucket)

# Empty all buckets
aws s3 rm s3://$IMAGES_BUCKET --recursive
aws s3 rm s3://$VIDEOS_BUCKET --recursive
aws s3 rm s3://$WEBAPP_BUCKET --recursive
aws s3 rm s3://$DEPLOY_BUCKET --recursive
```

### Step 2: Delete ECR Images

```bash
# Get repository name
ECR_REPO_NAME="ai-video-dev-lambda"

# Delete all images in the repository
aws ecr batch-delete-image \
  --repository-name $ECR_REPO_NAME \
  --image-ids "$(aws ecr list-images --repository-name $ECR_REPO_NAME --query 'imageIds[*]' --output json)" \
  --region ap-southeast-1 2>/dev/null || echo "No images to delete"
```

### Step 3: Destroy Infrastructure with Terraform

```bash
cd infra

# Review what will be destroyed
terraform plan -destroy -var-file=environments/dev.tfvars

# Destroy all resources (type 'yes' to confirm)
terraform destroy -var-file=environments/dev.tfvars
```

### Step 4: (Optional) Delete Terraform State Bucket

If you want to completely remove everything including the Terraform state:

```bash
# Empty and delete the state bucket
aws s3 rm s3://ai-video-terraform-state-YOUR-ACCOUNT-ID --recursive
aws s3 rb s3://ai-video-terraform-state-YOUR-ACCOUNT-ID
```

> **Warning:** Deleting the state bucket means you lose all Terraform state. Only do this if you're completely done with the project.

### Step 5: Clean Up Local Files

```bash
# Remove local build artifacts
rm -rf backend/package backend/deployment.zip
rm -rf frontend/dist frontend/node_modules
rm -rf infra/.terraform infra/tfplan
rm -f outputs.txt outputs.json
```

### Resources Destroyed

After running `terraform destroy`, the following will be deleted:

- All Lambda functions
- API Gateway
- DynamoDB tables (and all data)
- S3 buckets
- ECR repository
- Cognito User Pool (and all users)
- Step Functions state machine
- CloudWatch dashboards & alarms
- Secrets Manager secrets
- IAM roles and policies

> **Note:** CloudWatch Logs are retained by default. To delete them manually:
> ```bash
> for func in api agents tts video; do
>   aws logs delete-log-group --log-group-name /aws/lambda/ai-video-dev-$func-handler --region ap-southeast-1 2>/dev/null
> done
> ```
