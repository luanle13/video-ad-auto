# Architecture - AI Video Automation System

This document describes the system architecture, components, and data flows for the AI Video Automation Platform.

---

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND (React)                                │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Login     │  │  Dashboard  │  │  Products   │  │    Jobs     │        │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘        │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │ HTTPS
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           AWS API GATEWAY                                    │
│                    (REST API with Lambda Integration)                        │
└────────────────────────────────┬────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         API LAMBDA (FastAPI + Mangum)                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐     │
│  │  Auth    │  │ Products │  │   Jobs   │  │  Creds   │  │  Health  │     │
│  │ Routes   │  │  Routes  │  │  Routes  │  │  Routes  │  │  Check   │     │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘     │
└───────┬───────────────┬──────────────┬──────────────────────────────────────┘
        │               │              │
        ▼               ▼              ▼
┌───────────────┐ ┌───────────┐ ┌─────────────────────────────────────────────┐
│    Cognito    │ │  DynamoDB │ │              STEP FUNCTIONS                  │
│ (Auth/Users)  │ │ (Storage) │ │         (Video Pipeline Orchestration)       │
└───────────────┘ └───────────┘ └────────┬───────────────┬───────────────┬────┘
                                         │               │               │
                                         ▼               ▼               ▼
                               ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
                               │   AGENT     │  │    TTS      │  │   VIDEO     │
                               │   LAMBDA    │  │   LAMBDA    │  │   LAMBDA    │
                               │  (CrewAI)   │  │ (ElevenLabs)│  │  (Kling)    │
                               └──────┬──────┘  └──────┬──────┘  └──────┬──────┘
                                      │                │                │
                                      ▼                ▼                ▼
                               ┌─────────────┐  ┌─────────────┐  ┌─────────────┐
                               │  OpenAI     │  │ ElevenLabs  │  │  Kling AI   │
                               │  GPT-4o    │  │    API      │  │    API      │
                               └─────────────┘  └─────────────┘  └─────────────┘
```

---

## Component Descriptions

### Frontend Layer

| Component | Technology | Purpose |
|-----------|------------|---------|
| **React App** | React 18 + TypeScript | Single-page application |
| **Vite** | Build tool | Fast HMR and optimized builds |
| **TailwindCSS** | CSS framework | Responsive styling |
| **React Router** | Routing | Client-side navigation |
| **React Query** | Data fetching | Server state management |

**Key Pages:**
- `/login` - Authentication
- `/dashboard` - Job overview and statistics
- `/products` - Product management
- `/jobs` - Video generation jobs

### API Layer

| Component | Technology | Purpose |
|-----------|------------|---------|
| **API Gateway** | AWS API Gateway | HTTP endpoint, request routing |
| **API Lambda** | FastAPI + Mangum | REST API handling |
| **Cognito** | AWS Cognito | User authentication (JWT) |

**API Endpoints:**
- `POST /auth/register` - User registration
- `POST /auth/login` - User login
- `POST /auth/refresh` - Token refresh
- `GET /auth/me` - Current user profile
- `GET/POST /products` - Product CRUD
- `GET/POST /jobs` - Video job management
- `POST /jobs/{id}/regenerate` - Regenerate video

### Processing Layer

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Step Functions** | AWS Step Functions | Workflow orchestration |
| **Agent Lambda** | CrewAI + GPT-4o | Script and content generation |
| **TTS Lambda** | ElevenLabs API | Text-to-speech conversion |
| **Video Lambda** | Kling AI API | Video generation |

### Data Layer

| Component | Technology | Purpose |
|-----------|------------|---------|
| **DynamoDB** | AWS DynamoDB | User, product, job data |
| **S3** | AWS S3 | Images, audio, video storage |
| **Secrets Manager** | AWS Secrets Manager | API keys and credentials |

---

## Data Flow Diagrams

### Video Generation Flow

```
User                API                Step Functions        External APIs
  │                  │                       │                    │
  │ 1. Create Job    │                       │                    │
  │ ────────────────>│                       │                    │
  │                  │ 2. Store Job          │                    │
  │                  │ ─────────────────────>│                    │
  │                  │                       │ 3. Agent Task      │
  │                  │                       │ ──────────────────>│ OpenAI
  │                  │                       │<────── Script ─────│
  │                  │                       │                    │
  │                  │                       │ 4. TTS Task        │
  │                  │                       │ ──────────────────>│ ElevenLabs
  │                  │                       │<────── Audio ──────│
  │                  │                       │                    │
  │                  │                       │ 5. Video Task      │
  │                  │                       │ ──────────────────>│ Kling AI
  │                  │                       │<────── Video ──────│
  │                  │                       │                    │
  │                  │ 6. Job Complete       │                    │
  │<─ Status Update ─│<─────────────────────│                    │
  │                  │                       │                    │
```

### Authentication Flow

```
User                Frontend            API Gateway           Cognito
  │                    │                    │                    │
  │ 1. Login           │                    │                    │
  │ ──────────────────>│                    │                    │
  │                    │ 2. POST /auth/login│                    │
  │                    │ ──────────────────>│                    │
  │                    │                    │ 3. Authenticate    │
  │                    │                    │ ──────────────────>│
  │                    │                    │<─── JWT Tokens ────│
  │                    │<─── Tokens ────────│                    │
  │<─── Dashboard ─────│                    │                    │
  │                    │                    │                    │
```

---

## Technology Choices and Rationale

### Backend: Python + FastAPI

| Decision | Rationale |
|----------|-----------|
| **Python 3.13** | Modern features, excellent AI/ML ecosystem |
| **FastAPI** | High performance, automatic OpenAPI docs, type hints |
| **Mangum** | Seamless Lambda integration for FastAPI |
| **Pydantic v2** | Fast validation, excellent DX |

### AI/ML Stack

| Decision | Rationale |
|----------|-----------|
| **CrewAI** | Multi-agent orchestration, role-based AI collaboration |
| **GPT-4o** | Best-in-class language understanding and generation |
| **ElevenLabs** | High-quality, natural-sounding TTS |
| **Kling AI** | Specialized video generation for short-form content |

### Infrastructure: AWS Serverless

| Decision | Rationale |
|----------|-----------|
| **Lambda** | Pay-per-use, auto-scaling, no server management |
| **API Gateway** | Managed API hosting, throttling, caching |
| **Step Functions** | Visual workflow, error handling, retry logic |
| **DynamoDB** | Serverless NoSQL, on-demand scaling |
| **S3** | Durable object storage, lifecycle policies |
| **Cognito** | Managed auth, JWT tokens, MFA support |

### Frontend: React + Vite

| Decision | Rationale |
|----------|-----------|
| **React 18** | Component-based, large ecosystem, concurrent features |
| **TypeScript** | Type safety, better IDE support, fewer bugs |
| **Vite** | Fast development builds, optimized production |
| **TailwindCSS** | Utility-first, responsive, consistent styling |

### Infrastructure as Code

| Decision | Rationale |
|----------|-----------|
| **Terraform** | Multi-cloud support, declarative, state management |
| **GitHub Actions** | Native GitHub integration, matrix builds |

---

## DynamoDB Schema

### Users Table

| Attribute | Type | Key |
|-----------|------|-----|
| user_id | String | Partition Key |
| email | String | GSI |
| created_at | String | - |

### Products Table

| Attribute | Type | Key |
|-----------|------|-----|
| user_id | String | Partition Key |
| product_id | String | Sort Key |
| title | String | - |
| description | String | - |
| price | Number | - |
| image_keys | List | - |

### Jobs Table

| Attribute | Type | Key |
|-----------|------|-----|
| user_id | String | Partition Key |
| job_id | String | Sort Key |
| product_id | String | - |
| status | String | GSI |
| adjustments | Map | - |
| step_outputs | Map | - |
| video_key | String | - |
| audio_key | String | - |
| expires_at | Number | TTL |

---

## S3 Bucket Structure

```
ai-video-images/
├── {user_id}/
│   └── {product_id}/
│       └── {image_name}.jpg

ai-video-videos/
├── {user_id}/
│   └── {job_id}/
│       ├── audio.mp3
│       └── video.mp4

ai-video-webapp/
└── (Static website files)
```

---

## Security Architecture

### Authentication & Authorization

- **JWT-based authentication** via AWS Cognito
- **Token refresh** for long-lived sessions
- **Per-user data isolation** in DynamoDB

### Data Protection

- **Encryption at rest** - S3 SSE, DynamoDB encryption
- **Encryption in transit** - TLS 1.2+
- **Secrets management** - AWS Secrets Manager

### Network Security

- **API Gateway** - WAF integration, throttling
- **Lambda** - VPC optional, least-privilege IAM
- **CORS** - Strict origin validation

---

## Scalability Considerations

| Component | Scaling Strategy |
|-----------|------------------|
| API Lambda | Automatic (concurrent executions) |
| Agent Lambda | Reserved concurrency (cost control) |
| DynamoDB | On-demand capacity |
| S3 | Unlimited |
| Step Functions | 2,500 state transitions/second |

---

## Related Documents

- [Deployment Guide](/docs/deployment.md)
- [API Reference](/docs/api-reference.md)
- [Cost Analysis](/cost/analysis.md)
- [Incident Response](/docs/runbook/incident-response.md)
