# GitHub Actions Workflows

This document describes the GitHub Actions workflows and reusable actions for the AI Video Automation System.

## Workflows

### CI Workflow (`ci.yml`)
- **Trigger**: Push and PR to `main` and `develop` branches
- **Purpose**: Continuous Integration for code quality and testing
- **Jobs**:
  - `backend-lint`: Runs code linting and type checking
  - `backend-test`: Runs backend tests with coverage
  - `backend-security`: Runs security scanning with Trivy
  - `frontend-lint`: Runs frontend linting and type checking
  - `frontend-test`: Runs frontend tests with coverage
  - `frontend-build`: Builds the frontend application
  - `terraform-validate`: Validates Terraform configuration
  - `ci-success`: Final job that confirms all checks passed

### Deploy Dev Workflow (`deploy-dev.yml`)
- **Trigger**: Push to `develop` branch or manual dispatch
- **Purpose**: Deploy development environment
- **Jobs**:
  - `check-ci`: Verifies all CI checks passed
  - `deploy-backend`: Deploys backend Lambda functions
  - `deploy-infra`: Deploys infrastructure with Terraform
  - `deploy-frontend`: Deploys frontend to S3/CloudFront

### Deploy Prod Workflow (`deploy-prod.yml`)
- **Trigger**: Push to `main` branch or manual dispatch
- **Purpose**: Deploy production environment
- **Jobs**:
  - `check-ci`: Verifies all CI checks passed
  - `deploy-backend`: Deploys backend Lambda functions
  - `deploy-infra`: Deploys infrastructure with Terraform
  - `deploy-frontend`: Deploys frontend to S3/CloudFront
  - `notify`: Sends deployment notifications

## Reusable Actions

### Setup Python (`/.github/actions/setup-python`)
- **Purpose**: Sets up Python environment with caching and dependency installation
- **Inputs**:
  - `python-version`: Python version to use (default: '3.11')
  - `cache`: Enable pip cache (default: 'true')
  - `working-directory`: Working directory for dependency installation (default: '.')

### Setup Node (`/.github/actions/setup-node`)
- **Purpose**: Sets up Node.js environment with caching and dependency installation
- **Inputs**:
  - `node-version`: Node.js version to use (default: '20')
  - `cache`: Enable npm cache (default: 'true')
  - `working-directory`: Working directory for dependency installation (default: '.')

### AWS Auth (`/.github/actions/aws-auth`)
- **Purpose**: Configures AWS credentials with support for both OIDC and access keys
- **Inputs**:
  - `aws-region`: AWS region to use (default: 'us-east-1')
  - `role-to-assume`: AWS IAM role to assume (for OIDC)
  - `role-duration-seconds`: Duration for the assumed role (default: '3600')
  - `role-session-name`: Session name for the assumed role (default: 'GitHubActionSession')
  - `aws-access-key-id`: AWS Access Key ID (for access key authentication)
  - `aws-secret-access-key`: AWS Secret Access Key (for access key authentication)

## Required Secrets

The following secrets need to be configured in your GitHub repository:

### AWS Configuration
- `AWS_ACCOUNT_ID`: Your AWS account ID
- `ARTIFACTS_BUCKET`: S3 bucket for deployment artifacts
- `WEBAPP_BUCKET`: S3 bucket for web application
- `TERRAFORM_STATE_BUCKET`: S3 bucket for Terraform state
- `CLOUDFRONT_DISTRIBUTION_ID`: CloudFront distribution ID

### API Keys
- `OPENAI_API_KEY`: OpenAI API key
- `KLING_AI_API_KEY`: Kling AI API key
- `ELEVENLABS_API_KEY`: ElevenLabs API key

### Notifications
- `SLACK_WEBHOOK`: Slack webhook URL for deployment notifications

### OIDC Role
- `GITHUB_ACTIONS_ROLE_ARN`: ARN of the IAM role for GitHub Actions OIDC authentication

## Environment Setup

### Development Environment
1. Ensure all required secrets are configured in the GitHub repository
2. The development workflow runs on pushes to the `develop` branch
3. Requires approval for production deployments

### Production Environment
1. Ensure all required secrets are configured in the GitHub repository
2. The production workflow runs on pushes to the `main` branch
3. Requires manual approval for production deployments
4. Uses production-specific Terraform variables (`prod.tfvars`)

## Usage Examples

### Using Reusable Actions in Custom Workflows

```yaml
steps:
  - name: Setup Python
    uses: ./.github/actions/setup-python
    with:
      python-version: '3.11'
      working-directory: './backend'

  - name: Setup Node.js
    uses: ./.github/actions/setup-node
    with:
      node-version: '20'
      working-directory: './frontend'

  - name: Configure AWS
    uses: ./.github/actions/aws-auth
    with:
      aws-region: 'us-east-1'
      role-to-assume: ${{ secrets.GITHUB_ACTIONS_ROLE_ARN }}
```