# AI Video Automation System

Generate AI short-form videos from product images for TikTok, Shopee Vietnam, and Facebook Reels.

---

## Overview

The AI Video Automation System is a serverless platform that leverages AI technologies to automatically generate short-form marketing videos from product images. The system uses CrewAI agents to analyze products, generate engaging scripts, convert text to speech, and produce professional videos optimized for social media platforms.

**Key Features:**
- Automated video generation from product images
- AI-powered script generation using GPT-4.1
- Natural text-to-speech with ElevenLabs
- Video generation with DeepInfra Veo 3.1 Fast
- Multi-platform support (TikTok, Shopee, Facebook)
- User authentication and job management
- Cost-optimized serverless architecture

---

## Architecture

```
Frontend (React) → API Gateway → Lambda (FastAPI) → Step Functions
                                      ↓
                   ┌──────────────────┼──────────────────┐
                   ↓                  ↓                  ↓
            Agent Lambda        TTS Lambda         Video Lambda
            (CrewAI/GPT)       (ElevenLabs)     (DeepInfra Veo 3.1)
```

| Layer | Technology |
|-------|------------|
| **Frontend** | React 18 + Vite + TypeScript + TailwindCSS |
| **API** | FastAPI + Mangum (Lambda adapter) |
| **AI Agents** | CrewAI with OpenAI GPT-4.1 |
| **Video** | DeepInfra Veo 3.1 Fast |
| **TTS** | ElevenLabs (fallback: AWS Polly) |
| **Database** | DynamoDB (on-demand) |
| **Storage** | S3 with lifecycle policies |
| **Auth** | AWS Cognito (JWT) |
| **Orchestration** | AWS Step Functions |
| **IaC** | Terraform |
| **CI/CD** | GitHub Actions |
| **Region** | ap-southeast-1 (Singapore) |

---

## Quick Start

### Prerequisites

- **Node.js** 18+ (recommended: 20+)
- **Python** 3.11+ (recommended: 3.13)
- **AWS CLI** v2 (configured with credentials)
- **Terraform** 1.5+ (for infrastructure deployment only)

---

## Local Development Guide

This guide will help you run both the frontend and backend locally for development.

### Step 1: Clone the Repository

```bash
git clone https://github.com/luanle13/video-ad-auto.git
cd video-ad-auto
```

### Step 2: Backend Setup

#### 2.1 Create Python Virtual Environment

```bash
cd backend

# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
# macOS/Linux:
source .venv/bin/activate

# Windows (PowerShell):
.venv\Scripts\Activate.ps1

# Windows (CMD):
.venv\Scripts\activate.bat
```

#### 2.2 Install Dependencies

```bash
# Install production dependencies
pip install -r requirements.txt

# Install development dependencies (for testing)
pip install -e ".[dev]"
```

#### 2.3 Configure Environment Variables

Create a `.env` file in the `backend/` directory:

```bash
# Copy the template
cp .env.template .env
```

Edit `.env` with the following configuration:

```env
# Environment
ENVIRONMENT=dev
DEBUG=true

# AWS Configuration
AWS_REGION=ap-southeast-1

# Cognito (get these from AWS Console or Terraform output)
COGNITO_USER_POOL_ID=your-user-pool-id
COGNITO_CLIENT_ID=your-client-id
COGNITO_REGION=ap-southeast-1

# DynamoDB Tables
DYNAMODB_USERS_TABLE=ai-video-users
DYNAMODB_PRODUCTS_TABLE=ai-video-products
DYNAMODB_JOBS_TABLE=ai-video-jobs

# S3 Buckets (get from Terraform output)
S3_IMAGES_BUCKET=your-images-bucket
S3_VIDEOS_BUCKET=your-videos-bucket

# Frontend URL (for CORS)
FRONTEND_URL=http://localhost:5173

# Step Functions (optional for local development)
STEPFUNCTIONS_STATE_MACHINE_ARN=your-state-machine-arn

# Secrets Manager keys (optional - can use direct API keys for local dev)
SECRETS_OPENAI_KEY=ai-video-dev/openai-api-key
SECRETS_ELEVENLABS_KEY=ai-video-dev/elevenlabs-api-key
SECRETS_DEEPINFRA_KEY=ai-video-dev/deepinfra-api-key
```

**Note:** For local development, you need AWS credentials configured (`aws configure`) to access AWS services like Cognito, DynamoDB, and S3.

#### 2.4 Run the Backend Server

```bash
# Make sure you're in the backend directory with venv activated
cd backend
source .venv/bin/activate  # if not already activated

# Start the development server
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

The backend will be available at: **http://localhost:8000**

- API Documentation: http://localhost:8000/docs (Swagger UI)
- Health Check: http://localhost:8000/health

#### 2.5 Verify Backend is Running

```bash
curl http://localhost:8000/health
# Expected: {"status":"healthy","version":"0.1.0","timestamp":"..."}
```

---

### Step 3: Frontend Setup

#### 3.1 Install Dependencies

```bash
cd frontend

# Install npm packages
npm install
```

#### 3.2 Configure Environment Variables

Create a `.env.local` file in the `frontend/` directory:

```bash
touch .env.local
```

Add the following configuration:

```env
# API URL - points to local backend
VITE_API_URL=http://localhost:8000

# Cognito Configuration (get from AWS Console or Terraform output)
VITE_COGNITO_USER_POOL_ID=your-user-pool-id
VITE_COGNITO_CLIENT_ID=your-client-id
VITE_COGNITO_REGION=ap-southeast-1
```

**Note:** The Vite dev server has a proxy configured to forward `/api` requests to the backend at `http://localhost:8000`.

#### 3.3 Run the Frontend Development Server

```bash
# Make sure you're in the frontend directory
cd frontend

# Start the development server
npm run dev
```

The frontend will be available at: **http://localhost:5173**

#### 3.4 Verify Frontend is Running

Open your browser and navigate to http://localhost:5173. You should see the login page.

---

### Step 4: Running Both Together

For the full local development experience, you need both servers running:

**Terminal 1 - Backend:**
```bash
cd backend
source .venv/bin/activate
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

---

### Getting AWS Configuration Values

If you've deployed the infrastructure with Terraform, you can get the required values:

```bash
cd infra

# Get all outputs
terraform output

# Get specific values
terraform output cognito_user_pool_id
terraform output cognito_app_client_id
terraform output s3_images_bucket
terraform output s3_videos_bucket
```

---

### Troubleshooting Local Development

#### Backend Issues

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError` | Ensure venv is activated and dependencies are installed |
| `AWS credentials not found` | Run `aws configure` to set up credentials |
| Port 8000 in use | Use a different port: `uvicorn src.api.main:app --port 8001` |
| Cognito errors | Verify `COGNITO_USER_POOL_ID` and `COGNITO_CLIENT_ID` are correct |

#### Frontend Issues

| Problem | Solution |
|---------|----------|
| `npm install` fails | Delete `node_modules` and `package-lock.json`, then retry |
| API calls fail | Ensure backend is running on port 8000 |
| CORS errors | Check `FRONTEND_URL` in backend `.env` is set to `http://localhost:5173` |
| Port 5173 in use | Vite will automatically use the next available port |

---

### Running Tests

#### Backend Tests
```bash
cd backend
source .venv/bin/activate
pytest tests/ -v
```

#### Frontend Tests
```bash
cd frontend
npm test
```

---

### Infrastructure Deployment

For deploying to AWS (production):

```bash
cd infra

# Initialize Terraform
terraform init

# Review changes
terraform plan -var-file=environments/dev.tfvars

# Deploy infrastructure
terraform apply -var-file=environments/dev.tfvars
```

---

## Project Structure

```
.
├── backend/
│   ├── src/
│   │   ├── api/           # FastAPI application
│   │   ├── agents/        # CrewAI agents
│   │   ├── workers/       # Lambda workers (TTS, Video)
│   │   └── shared/        # Shared utilities
│   └── tests/             # pytest tests
├── frontend/
│   └── src/               # React application
├── infra/
│   └── modules/           # Terraform modules
├── docs/                  # Documentation
├── security/              # Security audits
└── specs/                 # OpenAPI specifications
```

---

## Documentation

### Core Documentation

| Document | Description |
|----------|-------------|
| [Architecture](/docs/architecture.md) | System design, components, data flows |
| [Deployment](/docs/deployment.md) | Step-by-step deployment guide |
| [API Reference](/docs/api-reference.md) | Complete API documentation |
| [Troubleshooting](/docs/troubleshooting.md) | Common issues and solutions |

### Operations

| Document | Description |
|----------|-------------|
| [Incident Response](/docs/runbook/incident-response.md) | Incident handling procedures |
| [Secrets Rotation](/docs/runbook/secrets-rotation.md) | API key rotation guide |

### Cost & Performance

| Document | Description |
|----------|-------------|
| [Cost Analysis](/cost/analysis.md) | Monthly cost estimates |
| [Lambda Sizing](/docs/cost/lambda-sizing.md) | Memory/timeout recommendations |
| [DynamoDB Optimization](/docs/cost/dynamodb-optimization.md) | Database cost optimization |

### Security

| Document | Description |
|----------|-------------|
| [Security Checklist](/security/checklist.md) | Security verification |
| [Input Validation](/security/input-validation.md) | Validation audit |
| [Logging Audit](/security/logging-audit.md) | PII protection |

---

## Testing

### Backend Tests

```bash
cd backend
source .venv/bin/activate
pytest tests/ -v --cov=src
```

### Frontend Tests

```bash
cd frontend
npm test
```

### Coverage Requirements

- Backend: >80% coverage
- Frontend: >70% coverage

---

## API Overview

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/auth/register` | POST | User registration |
| `/auth/login` | POST | User login |
| `/auth/refresh` | POST | Token refresh |
| `/auth/me` | GET | Current user profile |
| `/products` | GET/POST | Product management |
| `/jobs` | GET/POST | Video job management |
| `/jobs/{id}/regenerate` | POST | Regenerate video |
| `/health` | GET | Health check |

See [API Reference](/docs/api-reference.md) for complete documentation.

---

## Contributing

We welcome contributions! Please read our [Contributing Guidelines](./docs/CONTRIBUTING.md) before submitting PRs.

### Development Standards

- **Python**: PEP 8, type hints, Pydantic v2
- **TypeScript**: ESLint, Prettier
- **Testing**: pytest, Vitest
- **Commits**: Conventional commits

### Getting Help

- Create an issue for bugs or feature requests
- Check [Troubleshooting](/docs/troubleshooting.md) for common issues
- Review existing documentation before asking questions

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- [CrewAI](https://github.com/joaomdmoura/crewAI) - Multi-agent framework
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [ElevenLabs](https://elevenlabs.io/) - AI voice synthesis
- [DeepInfra](https://deepinfra.com/) - AI infrastructure (Veo 3.1 Fast video generation)