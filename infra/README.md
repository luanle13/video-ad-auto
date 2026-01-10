# AI Video Automation System - Infrastructure

This directory contains the Terraform configuration for the AI Video Automation System infrastructure.

## Architecture Overview

The infrastructure consists of:
- DynamoDB tables for user, product, and job data
- S3 buckets for images, videos, and deployment packages
- Lambda functions for TTS and video generation
- API Gateway for REST API endpoints
- Cognito for authentication
- Step Functions for workflow orchestration
- CloudFront for content delivery
- Monitoring and alerting systems
- Budget monitoring for cost control

## Prerequisites

Before deploying the infrastructure, ensure you have:

1. **AWS Account**: With appropriate permissions to create the required resources
2. **S3 Bucket for Terraform State**: Create an S3 bucket to store Terraform state files
3. **DynamoDB Table for State Locking**: Create a DynamoDB table for Terraform state locking (optional but recommended)
4. **AWS CLI**: Configured with appropriate credentials
5. **Terraform**: Version 1.6.0 or higher installed
6. **Secrets in AWS Secrets Manager**: API keys for external services (Anthropic, ElevenLabs, Kling AI)

## Deployment Instructions

### 1. Initialize Terraform

```bash
# Navigate to the infra directory
cd infra

# Initialize Terraform (downloads providers and modules)
terraform init \
  -backend-config="bucket=your-state-bucket-name" \
  -backend-config="key=ai-video-platform/terraform.tfstate" \
  -backend-config="region=ap-southeast-1" \
  -backend-config="dynamodb_table=your-lock-table-name" \
  -backend-config="encrypt=true"
```

### 2. Review Configuration

Review and update the variables in your `terraform.tfvars` file:

```hcl
project_name = "ai-video-platform"
environment = "dev"  # or "prod"
aws_region = "ap-southeast-1"

# Lambda configurations
lambda_timeout = 30
lambda_memory_size = 512
agent_lambda_timeout = 180
video_lambda_timeout = 600

# Budget configuration
monthly_budget_limit = 100  # Monthly budget in USD
notification_email = "admin@yourdomain.com"

# Cognito callback URLs
cognito_callback_urls = [
  "http://localhost:5173/callback",
  "http://localhost:3000/callback"
]
```

### 3. Plan the Deployment

```bash
# Review what changes will be made
terraform plan -var-file="environments/dev.tfvars"
```

### 4. Deploy the Infrastructure

```bash
# Apply the configuration
terraform apply -var-file="environments/dev.tfvars"

# Or apply with auto-approval (use with caution)
terraform apply -auto-approve -var-file="environments/dev.tfvars"
```

### 5. Verify Deployment

After deployment, Terraform will output important information like:
- API Gateway endpoint URL
- S3 bucket names
- DynamoDB table names
- Step Functions ARN

## Post-Deployment Steps

1. **Populate Secrets**: Add your API keys to AWS Secrets Manager:
   - `/ai-video-platform/dev/anthropic-api-key`
   - `/ai-video-platform/dev/elevenlabs-api-key`
   - `/ai-video-platform/dev/kling-api-key`

2. **Deploy Lambda Code**: Package and upload your Lambda function code to the deployment S3 bucket

3. **Configure DNS**: If using custom domains, update Route 53 records

## Destroying Infrastructure

To tear down all resources:

```bash
# Destroy all resources (use with caution!)
terraform destroy -var-file="environments/dev.tfvars"
```

## Troubleshooting

### Common Issues

1. **Permission Errors**: Ensure your AWS credentials have the required permissions
2. **S3 Bucket Conflicts**: Use unique bucket names to avoid conflicts
3. **API Key Issues**: Verify that secrets are properly stored in Secrets Manager
4. **Budget Notifications**: Check that the notification email is verified in SNS

### Useful Commands

```bash
# Show current state
terraform show

# List resources managed by Terraform
terraform state list

# Import existing resources (if needed)
terraform import aws_resource_type.name resource_identifier

# Refresh state with current AWS resources
terraform refresh
```

## Security Best Practices

- Store API keys in AWS Secrets Manager, not in Terraform variables
- Use IAM roles with least privilege principle
- Enable CloudTrail for API logging
- Use VPC endpoints for private access where needed
- Regularly rotate API keys in Secrets Manager

## Cost Management

- Monitor the budget notifications sent to your configured email
- Review the monthly cost reports in AWS Cost Explorer
- Adjust Lambda memory and timeout settings based on actual usage
- Use S3 Intelligent-Tiering for cost optimization

## Module Descriptions

- `api_gateway`: API Gateway with Cognito authentication
- `budget`: AWS Budgets for cost monitoring
- `cloudfront`: CloudFront distributions for content delivery
- `cognito`: Cognito User Pool and App Client for authentication
- `dynamodb`: DynamoDB tables for application data
- `lambda`: Lambda functions with IAM roles and policies
- `monitoring`: CloudWatch alarms and SNS notifications
- `s3`: S3 buckets for storage
- `secrets`: Secrets Manager entries for API keys
- `stepfunctions`: Step Functions state machines for orchestration