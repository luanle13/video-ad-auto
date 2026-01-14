# API Reference - AI Video Automation System

This document provides comprehensive API documentation for the AI Video Platform.

**Base URL:** `https://api.your-domain.com`

**Authentication:** Bearer token (JWT) in Authorization header

---

## Authentication

### Register User

Creates a new user account.

```http
POST /auth/register
Content-Type: application/json
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJjdHkiOiJKV1QiLCJlbmMiOiJBMjU2...",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

**Errors:**
| Code | Description |
|------|-------------|
| 400 | Invalid email format or weak password |
| 409 | User already exists |

---

### Login

Authenticates a user and returns tokens.

```http
POST /auth/login
Content-Type: application/json
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJjdHkiOiJKV1QiLCJlbmMiOiJBMjU2...",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

**Errors:**
| Code | Description |
|------|-------------|
| 401 | Invalid credentials |
| 429 | Too many login attempts |

---

### Refresh Token

Refreshes an expired access token.

```http
POST /auth/refresh
Content-Type: application/json
```

**Request Body:**
```json
{
  "refresh_token": "eyJjdHkiOiJKV1QiLCJlbmMiOiJBMjU2..."
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJjdHkiOiJKV1QiLCJlbmMiOiJBMjU2...",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

**Errors:**
| Code | Description |
|------|-------------|
| 401 | Invalid or expired refresh token |

---

### Get Current User

Returns the authenticated user's profile.

```http
GET /auth/me
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "user_id": "user-abc123def456",
  "email": "user@example.com",
  "created_at": "2025-01-15T10:30:00Z"
}
```

**Errors:**
| Code | Description |
|------|-------------|
| 401 | Missing or invalid token |

---

## Products

### Create Product

Creates a new product for video generation.

```http
POST /products
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "title": "Amazing Product",
  "description": "This product is designed to solve...",
  "price": 29.99,
  "image_keys": ["images/product1.jpg", "images/product2.jpg"]
}
```

**Response (201 Created):**
```json
{
  "product_id": "prod-xyz789",
  "user_id": "user-abc123",
  "title": "Amazing Product",
  "description": "This product is designed to solve...",
  "price": 29.99,
  "image_keys": ["images/product1.jpg", "images/product2.jpg"],
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-15T10:30:00Z"
}
```

**Errors:**
| Code | Description |
|------|-------------|
| 400 | Invalid request body |
| 401 | Unauthorized |

---

### List Products

Returns all products for the authenticated user.

```http
GET /products
Authorization: Bearer <access_token>
```

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| limit | integer | 50 | Maximum number of products to return |

**Response (200 OK):**
```json
{
  "products": [
    {
      "product_id": "prod-xyz789",
      "user_id": "user-abc123",
      "title": "Amazing Product",
      "description": "...",
      "price": 29.99,
      "image_keys": ["images/product1.jpg"],
      "created_at": "2025-01-15T10:30:00Z",
      "updated_at": "2025-01-15T10:30:00Z"
    }
  ],
  "count": 1
}
```

---

### Get Product

Returns a specific product by ID.

```http
GET /products/{product_id}
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "product_id": "prod-xyz789",
  "user_id": "user-abc123",
  "title": "Amazing Product",
  "description": "...",
  "price": 29.99,
  "image_keys": ["images/product1.jpg"],
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-15T10:30:00Z"
}
```

**Errors:**
| Code | Description |
|------|-------------|
| 404 | Product not found |

---

### Get Upload URL

Generates a presigned URL for uploading product images.

```http
GET /products/upload-url
Authorization: Bearer <access_token>
```

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| filename | string | Yes | Name of the file to upload |
| content_type | string | Yes | MIME type (e.g., "image/jpeg") |

**Response (200 OK):**
```json
{
  "upload_url": "https://bucket.s3.amazonaws.com/...",
  "key": "user-abc123/prod-xyz789/image.jpg"
}
```

---

## Jobs

### Create Job

Creates a new video generation job.

```http
POST /jobs
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "product_id": "prod-xyz789",
  "adjustments": {
    "tone": "professional",
    "duration": 30,
    "language": "vi",
    "voice_id": "voice-123"
  }
}
```

**Adjustments Options:**
| Field | Type | Options | Description |
|-------|------|---------|-------------|
| tone | string | professional, casual, humorous | Video tone |
| duration | integer | 15, 30, 60 | Video duration in seconds |
| language | string | en, vi | Script language |
| voice_id | string | - | ElevenLabs voice ID |
| platform | string | tiktok, shopee, facebook | Target platform |

**Response (201 Created):**
```json
{
  "job_id": "job-abc123",
  "user_id": "user-abc123",
  "product_id": "prod-xyz789",
  "status": "PENDING",
  "adjustments": {
    "tone": "professional",
    "duration": 30
  },
  "step_outputs": {},
  "video_url": null,
  "audio_url": null,
  "error_message": null,
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-15T10:30:00Z"
}
```

---

### List Jobs

Returns all jobs for the authenticated user.

```http
GET /jobs
Authorization: Bearer <access_token>
```

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| status | string | - | Filter by status (PENDING, PROCESSING, COMPLETE, FAILED) |
| limit | integer | 50 | Maximum number of jobs to return |

**Response (200 OK):**
```json
{
  "jobs": [
    {
      "job_id": "job-abc123",
      "user_id": "user-abc123",
      "product_id": "prod-xyz789",
      "status": "COMPLETE",
      "adjustments": {...},
      "step_outputs": {...},
      "video_url": "https://...",
      "audio_url": "https://...",
      "error_message": null,
      "created_at": "2025-01-15T10:30:00Z",
      "updated_at": "2025-01-15T10:35:00Z"
    }
  ],
  "count": 1
}
```

---

### Get Job

Returns a specific job by ID.

```http
GET /jobs/{job_id}
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "job_id": "job-abc123",
  "user_id": "user-abc123",
  "product_id": "prod-xyz789",
  "status": "COMPLETE",
  "adjustments": {
    "tone": "professional",
    "duration": 30
  },
  "step_outputs": {
    "script": "Introducing our amazing product...",
    "audio_key": "audio/job-abc123/audio.mp3",
    "video_key": "videos/job-abc123/video.mp4"
  },
  "video_url": "https://presigned-url...",
  "audio_url": "https://presigned-url...",
  "error_message": null,
  "created_at": "2025-01-15T10:30:00Z",
  "updated_at": "2025-01-15T10:35:00Z"
}
```

**Job Status Values:**
| Status | Description |
|--------|-------------|
| PENDING | Job created, awaiting processing |
| PROCESSING | Job is being processed |
| COMPLETE | Job completed successfully |
| FAILED | Job failed with error |

---

### Regenerate Job

Creates a new job based on an existing one with updated adjustments.

```http
POST /jobs/{job_id}/regenerate
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "adjustments": {
    "tone": "humorous"
  }
}
```

**Response (201 Created):**
```json
{
  "job_id": "job-def456",
  "user_id": "user-abc123",
  "product_id": "prod-xyz789",
  "status": "PENDING",
  "adjustments": {
    "tone": "humorous",
    "duration": 30
  },
  ...
}
```

**Errors:**
| Code | Description |
|------|-------------|
| 400 | Cannot regenerate job in current status |
| 404 | Original job not found |

---

### Get Video Download URL

Returns a presigned download URL for the generated video.

```http
GET /jobs/{job_id}/video
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "download_url": "https://bucket.s3.amazonaws.com/..."
}
```

**Errors:**
| Code | Description |
|------|-------------|
| 400 | Video not available (job not complete) |
| 404 | Job not found |

---

## Credentials

### Store Platform Credentials

Stores credentials for external platforms (TikTok, Shopee, etc.).

```http
POST /credentials
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**
```json
{
  "platform": "tiktok",
  "access_token": "...",
  "refresh_token": "...",
  "expires_at": "2025-02-15T10:30:00Z"
}
```

**Response (201 Created):**
```json
{
  "credential_id": "cred-abc123",
  "user_id": "user-abc123",
  "platform": "tiktok",
  "created_at": "2025-01-15T10:30:00Z"
}
```

---

### List Platform Credentials

Returns all stored credentials for the user.

```http
GET /credentials
Authorization: Bearer <access_token>
```

**Response (200 OK):**
```json
{
  "credentials": [
    {
      "credential_id": "cred-abc123",
      "platform": "tiktok",
      "created_at": "2025-01-15T10:30:00Z"
    }
  ]
}
```

---

## Health Check

### Check API Health

```http
GET /health
```

**Response (200 OK):**
```json
{
  "status": "healthy",
  "environment": "prod",
  "timestamp": "2025-01-15T10:30:00Z"
}
```

---

## Error Responses

All error responses follow this format:

```json
{
  "detail": {
    "message": "Human-readable error message",
    "code": "ERROR_CODE",
    "field": "field_name"  // Optional, for validation errors
  }
}
```

### Common Error Codes

| HTTP Code | Error Code | Description |
|-----------|------------|-------------|
| 400 | VALIDATION_ERROR | Invalid request body |
| 401 | UNAUTHORIZED | Missing or invalid token |
| 403 | FORBIDDEN | Insufficient permissions |
| 404 | NOT_FOUND | Resource not found |
| 409 | CONFLICT | Resource already exists |
| 429 | RATE_LIMITED | Too many requests |
| 500 | INTERNAL_ERROR | Server error |

---

## Rate Limits

| Endpoint | Limit |
|----------|-------|
| `/auth/*` | 10 requests/minute |
| All other endpoints | 60 requests/minute |

Rate limit headers:
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 55
X-RateLimit-Reset: 1705317060
```

---

## SDK Examples

### Python

```python
import requests

BASE_URL = "https://api.your-domain.com"

# Login
response = requests.post(f"{BASE_URL}/auth/login", json={
    "email": "user@example.com",
    "password": "password"
})
tokens = response.json()

# Create job
headers = {"Authorization": f"Bearer {tokens['access_token']}"}
response = requests.post(f"{BASE_URL}/jobs", headers=headers, json={
    "product_id": "prod-xyz789",
    "adjustments": {"tone": "professional"}
})
job = response.json()
```

### JavaScript

```javascript
const BASE_URL = "https://api.your-domain.com";

// Login
const loginResponse = await fetch(`${BASE_URL}/auth/login`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ email: "user@example.com", password: "password" })
});
const tokens = await loginResponse.json();

// Create job
const jobResponse = await fetch(`${BASE_URL}/jobs`, {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    "Authorization": `Bearer ${tokens.access_token}`
  },
  body: JSON.stringify({ product_id: "prod-xyz789", adjustments: { tone: "professional" } })
});
const job = await jobResponse.json();
```

---

## Related Documents

- [Architecture Overview](/docs/architecture.md)
- [Deployment Guide](/docs/deployment.md)
- [Troubleshooting](/docs/troubleshooting.md)
