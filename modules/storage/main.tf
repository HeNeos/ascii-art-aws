resource "aws_s3_bucket" "media" {
  bucket = "media-bucket-${var.stage}-${var.account_id}"

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_s3_bucket_versioning" "media" {
  depends_on = [aws_s3_bucket.media]
  bucket     = aws_s3_bucket.media.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_cors_configuration" "media" {
  bucket = aws_s3_bucket.media.id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET", "PUT", "POST", "HEAD"]
    allowed_origins = [
      "https://v0-image-analysis-cyan-delta.vercel.app" // TODO: replace with valid origins
    ]
    expose_headers  = ["ETag"]
    max_age_seconds = 3000
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "media" {
  depends_on = [aws_s3_bucket_versioning.media]
  bucket     = aws_s3_bucket.media.id
  rule {
    id = "Delete old files"
    expiration {
      days = 1
    }
    status = "Enabled"
  }
}

resource "aws_s3_bucket" "audio" {
  bucket = "audio-bucket-${var.stage}-${var.account_id}"

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_s3_bucket_versioning" "audio" {
  depends_on = [aws_s3_bucket.audio]
  bucket     = aws_s3_bucket.audio.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "audio" {
  depends_on = [aws_s3_bucket_versioning.audio]
  bucket     = aws_s3_bucket.audio.id
  rule {
    id = "Delete old files"
    expiration {
      days = 1
    }
    status = "Enabled"
  }
}

resource "aws_s3_bucket" "ascii_art" {
  bucket = "ascii-art-bucket-${var.stage}-${var.account_id}"

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_s3_bucket_versioning" "ascii_art" {
  depends_on = [aws_s3_bucket.ascii_art]
  bucket     = aws_s3_bucket.ascii_art.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "ascii_art" {
  depends_on = [aws_s3_bucket_versioning.ascii_art]
  bucket     = aws_s3_bucket.ascii_art.id
  rule {
    id = "Delete old files"
    expiration {
      days = 2
    }
    status = "Enabled"
  }
}

resource "aws_s3_bucket_cors_configuration" "ascii_art" {
  bucket = aws_s3_bucket.ascii_art.id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET", "HEAD"]
    allowed_origins = ["*"]
    expose_headers  = ["ETag"]
    max_age_seconds = 3000
  }
}

resource "aws_s3_bucket" "r2_secrets" {
  bucket = "r2-secrets-bucket-${var.stage}-${var.account_id}"

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_s3_bucket_versioning" "r2_secrets" {
  depends_on = [aws_s3_bucket.r2_secrets]
  bucket     = aws_s3_bucket.r2_secrets.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_object" "r2_secrets" {
  bucket                 = aws_s3_bucket.r2_secrets.id
  key                    = "r2_secrets.json"
  source                 = "r2_secrets.json"
  server_side_encryption = "AES256"
  etag                   = filemd5("r2_secrets.json")
}

resource "aws_s3_bucket_public_access_block" "r2_secrets" {
  bucket = aws_s3_bucket.r2_secrets.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

data "aws_iam_policy_document" "r2_secrets" {
  statement {
    actions   = ["s3:GetObject"]
    resources = ["${aws_s3_bucket.r2_secrets.arn}/r2_secrets.json"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
    condition {
      test     = "StringLike"
      variable = "aws:PrincipalArn"
      values   = ["arn:aws:iam::${var.account_id}:role/*"]
    }
  }
  statement {
    effect    = "Deny"
    actions   = ["s3:*"]
    resources = [aws_s3_bucket.r2_secrets.arn, "${aws_s3_bucket.r2_secrets.arn}/*"]
    principals {
      type        = "*"
      identifiers = ["*"]
    }
    condition {
      test     = "Bool"
      variable = "aws:SecureTransport"
      values   = ["false"]
    }
  }
}

resource "aws_s3_bucket_policy" "r2_secrets" {
  bucket = aws_s3_bucket.r2_secrets.id
  policy = data.aws_iam_policy_document.r2_secrets.json
}
