resource "aws_s3_bucket" "images" {
  bucket = "${var.name_prefix}-images-${var.name_suffix}"

  tags = {
    Name        = "${var.name_prefix}-images"
    Environment = var.environment
    Module      = "s3"
  }
}

resource "aws_s3_bucket_versioning" "images" {
  bucket = aws_s3_bucket.images.id

  versioning_configuration {
    status = "Disabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "images" {
  bucket = aws_s3_bucket.images.bucket

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "images" {
  bucket = aws_s3_bucket.images.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_cors_configuration" "images" {
  bucket = aws_s3_bucket.images.id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["PUT", "POST", "GET"]
    allowed_origins = ["*"] # Allow from any origin for presigned uploads
    max_age_seconds = 3000
  }
}

resource "aws_s3_bucket" "videos" {
  bucket = "${var.name_prefix}-videos-${var.name_suffix}"

  tags = {
    Name        = "${var.name_prefix}-videos"
    Environment = var.environment
    Module      = "s3"
  }
}

resource "aws_s3_bucket_versioning" "videos" {
  bucket = aws_s3_bucket.videos.id

  versioning_configuration {
    status = "Disabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "videos" {
  bucket = aws_s3_bucket.videos.bucket

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "videos" {
  bucket = aws_s3_bucket.videos.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "videos" {
  bucket = aws_s3_bucket.videos.id

  rule {
    id     = "expire-old-videos"
    status = "Enabled"

    filter {
      prefix = "" # Apply to all objects in the bucket
    }

    expiration {
      days = var.lifecycle_expiration_days
    }
  }

  rule {
    id     = "transition-to-ia"
    status = "Enabled"

    filter {
      prefix = "" # Apply to all objects in the bucket
    }

    transition {
      days          = 7
      storage_class = "STANDARD_IA"
    }
  }
}

# Intelligent-Tiering for images bucket - optimizes costs for unpredictable access patterns
resource "aws_s3_bucket_intelligent_tiering_configuration" "images" {
  bucket = aws_s3_bucket.images.id
  name   = "optimize-storage-costs"

  tiering {
    access_tier = "ARCHIVE_ACCESS"
    days        = 90
  }

  tiering {
    access_tier = "DEEP_ARCHIVE_ACCESS"
    days        = 180
  }
}

# Lifecycle rule to enable Intelligent-Tiering for all objects in images bucket
resource "aws_s3_bucket_lifecycle_configuration" "images" {
  bucket = aws_s3_bucket.images.id

  rule {
    id     = "intelligent-tiering"
    status = "Enabled"

    filter {
      prefix = "" # Apply to all objects
    }

    transition {
      days          = 0
      storage_class = "INTELLIGENT_TIERING"
    }
  }
}

resource "aws_s3_bucket" "webapp" {
  bucket = "${var.name_prefix}-webapp-${var.name_suffix}"

  tags = {
    Name        = "${var.name_prefix}-webapp"
    Environment = var.environment
    Module      = "s3"
  }
}

resource "aws_s3_bucket_versioning" "webapp" {
  bucket = aws_s3_bucket.webapp.id

  versioning_configuration {
    status = "Disabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "webapp" {
  bucket = aws_s3_bucket.webapp.bucket

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "webapp" {
  bucket = aws_s3_bucket.webapp.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}