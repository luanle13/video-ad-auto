# AI Video Automation System

Generate AI short-form videos from product images for TikTok, Shopee Vietnam, Facebook Reels.

## Overview

The AI Video Automation System is a comprehensive solution that leverages AI technologies to automatically generate short-form videos from product images. The system uses CrewAI agents to analyze products and generate engaging video content, with support for multiple social media platforms.

## Architecture

- **Backend**: Python 3.13.3 with FastAPI and Mangum (Lambda adapter)
- **AI Agents**: CrewAI with Open AI GPT 4.1
- **Video Generation**: Kling AI API
- **TTS**: ElevenLabs API (fallback: AWS Polly)
- **Frontend**: React 18 + Vite + TypeScript + TailwindCSS
- **Database**: DynamoDB (on-demand)
- **Storage**: S3
- **Auth**: AWS Cognito
- **Orchestration**: AWS Step Functions
- **IaC**: Terraform
- **CI/CD**: GitHub Actions

## Quick Start

### Prerequisites

- Node.js 18+
- Python 3.13+
- AWS CLI configured
- Docker (optional)

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. Run the backend:
   ```bash
   uvicorn src.api.main:app --reload
   ```

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. Run the frontend:
   ```bash
   npm run dev
   ```

### Infrastructure Setup

1. Navigate to the infra directory:
   ```bash
   cd infra
   ```

2. Initialize Terraform:
   ```bash
   terraform init
   ```

3. Apply infrastructure:
   ```bash
   terraform apply
   ```

## Documentation

- [API Documentation](./specs/)
- [Architecture Diagrams](./docs/architecture.md)
- [Deployment Guide](./docs/deployment.md)
- [Contributing Guidelines](./docs/CONTRIBUTING.md)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.