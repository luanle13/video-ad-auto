# CloudFront Origin Access Identity for S3 access
resource "aws_cloudfront_origin_access_identity" "main" {
  comment = "${var.name_prefix}-s3-oai"
}

# CloudFront Distribution for S3 bucket
resource "aws_cloudfront_distribution" "main" {
  origin {
    domain_name = var.s3_bucket_regional_domain_name
    origin_id   = "${var.name_prefix}-s3-origin"

    s3_origin_config {
      origin_access_identity = aws_cloudfront_origin_access_identity.main.cloudfront_access_identity_path
    }
  }

  enabled             = true
  is_ipv6_enabled     = true
  default_root_object = "index.html"

  # Aliases can be added later if needed
  aliases = []

  # Default cache behavior
  default_cache_behavior {
    allowed_methods        = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "${var.name_prefix}-s3-origin"
    
    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }

    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 3600
    max_ttl                = 86400
    compress               = true
  }

  # Price class - restricting to Asia Pacific for cost optimization
  price_class = "PriceClass_All"

  # Restrictions
  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  # Web ACL for security (can be added later if needed)
  # web_acl_id = aws_waf_web_acl.example.arn

  # Certificate ARN for HTTPS (can be added later if needed)
  # viewer_certificate {
  #   acm_certificate_arn = aws_acm_certificate.example.arn
  #   ssl_support_method  = "sni-only"
  # }

  # For now, using default cloudfront certificate
  viewer_certificate {
    cloudfront_default_certificate = true
  }

  # Custom error responses for SPA (Single Page Application) support
  custom_error_response {
    error_code            = 404
    response_code         = 200
    response_page_path    = "/index.html"
    error_caching_min_ttl = 0
  }

  custom_error_response {
    error_code            = 403
    response_code         = 200
    response_page_path    = "/index.html"
    error_caching_min_ttl = 0
  }

  tags = {
    Name        = "${var.name_prefix}-cloudfront-distribution"
    Environment = "production"  # Using default since environment isn't in variables
    Module      = "cloudfront"
  }
}

# S3 Bucket Policy to allow CloudFront to access the bucket
resource "aws_s3_bucket_policy" "main" {
  bucket = var.s3_bucket_id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowCloudFrontServicePrincipal"
        Effect = "Allow"
        Principal = {
          Service = "cloudfront.amazonaws.com"
        }
        Action   = "s3:GetObject"
        Resource = "${var.s3_bucket_arn}/*"
        Condition = {
          StringEquals = {
            "AWS:SourceArn" = aws_cloudfront_origin_access_identity.main.iam_arn
          }
        }
      }
    ]
  })

  depends_on = [aws_cloudfront_distribution.main]
}