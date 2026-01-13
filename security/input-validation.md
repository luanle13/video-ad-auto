# Input Validation Audit - AI Video Automation System

This document audits all input validation across the API endpoints and file uploads.

---

## API Endpoints

### POST /auth/register

**Request Model**: `RegisterRequest` (`backend/src/api/models/auth.py:5`)

| Field | Type | Validation | Status |
|-------|------|------------|--------|
| `email` | `EmailStr` | Pydantic email format validation | OK |
| `password` | `str` | `min_length=8`, `max_length=128` | PARTIAL |

**Gaps Identified**:
- Password complexity rules not enforced (uppercase, lowercase, numbers, special chars)
- No rate limiting on registration endpoint

**Recommendations**:
```python
password: str = Field(
    ...,
    min_length=8,
    max_length=128,
    pattern=r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$",
)
```

---

### POST /auth/login

**Request Model**: `LoginRequest` (`backend/src/api/models/auth.py:12`)

| Field | Type | Validation | Status |
|-------|------|------------|--------|
| `email` | `EmailStr` | Pydantic email format validation | OK |
| `password` | `str` | No constraints | MISSING |

**Gaps Identified**:
- No minimum length on password field
- No rate limiting to prevent brute force attacks

**Recommendations**:
- Add `min_length=1` to prevent empty password attempts
- Implement rate limiting (5 attempts per minute per IP)

---

### POST /auth/refresh

**Request Model**: `RefreshRequest` (`backend/src/api/models/auth.py:28`)

| Field | Type | Validation | Status |
|-------|------|------------|--------|
| `refresh_token` | `str` | No constraints | PARTIAL |

**Notes**: Token validation handled by Cognito client at runtime.

---

### POST /products

**Request Model**: `CreateProductRequest` (`backend/src/api/models/products.py:24`)

| Field | Type | Validation | Status |
|-------|------|------------|--------|
| `title` | `str` | `min_length=1`, `max_length=200` | OK |
| `description` | `str` | `min_length=1`, `max_length=2000` | OK |
| `price` | `str` | Pattern: `^\d+(\.\d{1,2})?$` | OK |
| `image_keys` | `list[str]` | `min_length=1`, `max_length=5` | PARTIAL |

**Gaps Identified**:
- No validation on individual `image_keys` format (should be S3 key pattern)
- No XSS sanitization on `title` and `description`
- No validation that image_keys exist in S3

**Recommendations**:
```python
image_keys: list[str] = Field(
    ...,
    min_length=1,
    max_length=5,
    description="S3 keys for product images",
)

@field_validator("image_keys")
@classmethod
def validate_image_keys(cls, v: list[str]) -> list[str]:
    pattern = re.compile(r"^[\w-]+/[\w-]+/[\w-]+\.(jpg|jpeg|png|webp)$")
    for key in v:
        if not pattern.match(key):
            raise ValueError(f"Invalid image key format: {key}")
    return v
```

---

### PUT /products/{product_id}

**Request Model**: `UpdateProductRequest` (`backend/src/api/models/products.py:33`)

| Field | Type | Validation | Status |
|-------|------|------------|--------|
| `title` | `str \| None` | `min_length=1`, `max_length=200` | OK |
| `description` | `str \| None` | `min_length=1`, `max_length=2000` | OK |
| `price` | `str \| None` | Pattern: `^\d+(\.\d{1,2})?$` | OK |

**Path Parameter**:
- `product_id`: No format validation (should be UUID)

**Recommendations**:
- Add UUID format validation for `product_id` path parameter

---

### POST /jobs

**Request Model**: `CreateJobRequest` (`backend/src/api/models/jobs.py:31`)

| Field | Type | Validation | Status |
|-------|------|------------|--------|
| `product_id` | `str` | No format validation | MISSING |
| `adjustments` | `JobAdjustments \| None` | See below | PARTIAL |

**JobAdjustments Model** (`backend/src/api/models/jobs.py:21`):

| Field | Type | Validation | Status |
|-------|------|------------|--------|
| `background_style` | `str \| None` | No constraints | MISSING |
| `tone` | `str \| None` | No constraints | MISSING |
| `emphasis` | `str \| None` | No constraints | MISSING |
| `duration_preference` | `int \| None` | `ge=30`, `le=60` | OK |
| `additional_instructions` | `str \| None` | `max_length=500` | OK |

**Gaps Identified**:
- `product_id` should validate UUID format
- `background_style`, `tone`, `emphasis` have no length limits (DoS risk with large strings)
- No sanitization for prompt injection in adjustment fields

**Recommendations**:
```python
product_id: str = Field(..., pattern=r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")

background_style: str | None = Field(None, max_length=50)
tone: str | None = Field(None, max_length=50)
emphasis: str | None = Field(None, max_length=100)
```

---

### POST /jobs/{job_id}/regenerate

**Request Model**: `RegenerateJobRequest` (`backend/src/api/models/jobs.py:38`)

| Field | Type | Validation | Status |
|-------|------|------------|--------|
| `adjustments` | `JobAdjustments` | Same as above | PARTIAL |

**Path Parameter**:
- `job_id`: No format validation (should be UUID)

---

### PUT /credentials

**Request Model**: `PlatformCredentialsRequest` (`backend/src/api/models/credentials.py:27`)

**TikTokCredentials**:
| Field | Type | Validation | Status |
|-------|------|------------|--------|
| `access_token` | `str` | `min_length=1` | PARTIAL |

**ShopeeCredentials**:
| Field | Type | Validation | Status |
|-------|------|------------|--------|
| `shop_id` | `str` | No constraints | MISSING |
| `access_token` | `str` | `min_length=1` | PARTIAL |

**FacebookCredentials**:
| Field | Type | Validation | Status |
|-------|------|------------|--------|
| `page_id` | `str` | No constraints | MISSING |
| `access_token` | `str` | `min_length=1` | PARTIAL |

**Gaps Identified**:
- `shop_id` and `page_id` have no format validation
- Access tokens have no max length (potential DoS)

**Recommendations**:
```python
shop_id: str = Field(..., min_length=1, max_length=50, pattern=r"^\d+$")
page_id: str = Field(..., min_length=1, max_length=50, pattern=r"^\d+$")
access_token: str = Field(..., min_length=1, max_length=2048)
```

---

### DELETE /credentials/{platform}

**Path Parameter**:
| Parameter | Validation | Status |
|-----------|------------|--------|
| `platform` | Runtime check: tiktok, shopee, facebook | OK |

**Notes**: Uses runtime validation with explicit whitelist.

---

## File Uploads

### Image Upload Request

**Request Model**: `ImageUploadRequest` (`backend/src/api/models/products.py:5`)

| Field | Type | Validation | Status |
|-------|------|------------|--------|
| `filename` | `str` | No constraints | MISSING |
| `content_type` | `str` | Pattern: `^image/(jpeg\|png\|webp)$` | OK |

### S3 Upload Validation

**Implementation**: `S3Client.generate_upload_url()` (`backend/src/shared/storage.py:41`)

| Constraint | Value | Status |
|------------|-------|--------|
| Allowed types | `image/jpeg`, `image/png`, `image/webp` | OK |
| Min size | 1 byte | OK |
| Max size | 5MB (5,242,880 bytes) | OK |
| Max files | 5 per product (model level) | OK |

**Gaps Identified**:
- Filename not validated (path traversal risk)
- No file extension validation (only MIME type)
- Content-Type header can be spoofed client-side
- No virus/malware scanning

**Recommendations**:
1. Add filename validation:
```python
filename: str = Field(
    ...,
    min_length=1,
    max_length=255,
    pattern=r"^[\w\-. ]+\.(jpg|jpeg|png|webp)$",
)
```

2. Add server-side content-type validation on S3:
```python
# Add S3 bucket policy for content-type validation
# Or use Lambda@Edge for upload validation
```

3. Sanitize filename in key generation:
```python
def generate_image_key(self, user_id: str, product_id: str, filename: str) -> str:
    # Sanitize filename to prevent path traversal
    safe_filename = re.sub(r"[^\w\-.]", "", filename)
    ext = safe_filename.rsplit(".", 1)[-1] if "." in safe_filename else "jpg"
    if ext.lower() not in ["jpg", "jpeg", "png", "webp"]:
        ext = "jpg"
    return f"{user_id}/{product_id}/{uuid4()}.{ext}"
```

---

## Global Validation Gaps

### Missing Rate Limiting

| Endpoint | Risk | Priority |
|----------|------|----------|
| POST /auth/login | Brute force attacks | HIGH |
| POST /auth/register | Account enumeration, spam | HIGH |
| POST /jobs | Resource exhaustion | MEDIUM |
| POST /products/upload-url | Storage abuse | MEDIUM |

**Recommendation**: Implement API Gateway throttling or custom rate limiting:
```hcl
# Terraform - API Gateway throttling
resource "aws_api_gateway_method_settings" "settings" {
  settings {
    throttling_burst_limit = 10
    throttling_rate_limit  = 5
  }
}
```

### Missing Request Size Limits

**Recommendation**: Add global request body size limit:
```python
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    MAX_SIZE = 1024 * 1024  # 1MB

    async def dispatch(self, request: Request, call_next):
        if request.headers.get("content-length"):
            if int(request.headers["content-length"]) > self.MAX_SIZE:
                raise HTTPException(413, "Request too large")
        return await call_next(request)
```

### Missing XSS Sanitization

Fields requiring sanitization:
- `CreateProductRequest.title`
- `CreateProductRequest.description`
- `JobAdjustments.additional_instructions`
- `JobAdjustments.emphasis`

**Recommendation**: Add HTML sanitization validator:
```python
import html

@field_validator("title", "description", mode="after")
@classmethod
def sanitize_html(cls, v: str) -> str:
    return html.escape(v)
```

---

## Validation Summary

| Category | Total Fields | Validated | Gaps |
|----------|--------------|-----------|------|
| Auth endpoints | 6 | 4 | 2 |
| Product endpoints | 8 | 7 | 1 |
| Job endpoints | 8 | 3 | 5 |
| Credential endpoints | 6 | 3 | 3 |
| File uploads | 2 | 1 | 1 |
| **Total** | **30** | **18** | **12** |

**Validation Coverage**: 60%

---

## Priority Remediation Plan

### HIGH Priority (Address Immediately)
1. Add password complexity validation on registration
2. Add rate limiting on auth endpoints
3. Add length limits to JobAdjustments string fields
4. Validate product_id/job_id as UUID format
5. Sanitize filename in image uploads

### MEDIUM Priority (Address Soon)
1. Add XSS sanitization on text inputs
2. Add shop_id/page_id format validation
3. Add request size limits globally
4. Add server-side content-type verification

### LOW Priority (Address When Possible)
1. Add virus scanning for uploads
2. Add file extension validation
3. Enhance token format validation

---

## Related Documents

- [Security Checklist](/security/checklist.md)
- [IAM Audit](/security/iam-audit.md)
- [OWASP Input Validation Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html)
