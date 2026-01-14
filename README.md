# AI Video Automation System

Generate AI short-form videos from product images for TikTok, Shopee Vietnam, and Facebook Reels.

---

## Overview

The AI Video Automation System is a serverless platform that leverages AI technologies to automatically generate short-form marketing videos from product images. The system uses CrewAI agents to analyze products, generate engaging scripts, convert text to speech, and produce professional videos optimized for social media platforms.

**Key Features:**
- Automated video generation from product images
- AI-powered script generation using GPT-4.1
- Natural text-to-speech with ElevenLabs
- Video generation with Kling AI
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
            (CrewAI/GPT)       (ElevenLabs)        (Kling AI)
```

| Layer | Technology |
|-------|------------|
| **Frontend** | React 18 + Vite + TypeScript + TailwindCSS |
| **API** | FastAPI + Mangum (Lambda adapter) |
| **AI Agents** | CrewAI with OpenAI GPT-4.1 |
| **Video** | Kling AI API |
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

- Node.js 18+
- Python 3.13+
- AWS CLI v2 (configured)
- Terraform 1.5+

### Backend Setup

```bash
cd backend

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Run locally
uvicorn src.api.main:app --reload
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Run development server
npm run dev
```

### Infrastructure Deployment

```bash
cd infra

# Initialize Terraform
terraform init

# Review changes
terraform plan

# Deploy infrastructure
terraform apply
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
- [Kling AI](https://klingai.com/) - Video generation