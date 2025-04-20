locals {
  buckets = {
    media = {
      name_prefix     = "media-bucket"
      expiration_days = 1
    },
    audio = {
      name_prefix     = "audio-bucket"
      expiration_days = 1
    },
    ascii_art = {
      name_prefix     = "ascii-art-bucket"
      expiration_days = 1
    }
  }
}

resource "aws_s3_bucket" "bucket" {
  for_each = local.buckets
  bucket = "${each.value.name_prefix}-${var.stage}-${var.account_id}"
  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_s3_bucket_versioning" "versioning" {
  for_each = local.buckets
  bucket = aws_s3_bucket.bucket[each.key].id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "buckets_config" {
  for_each = local.buckets
  bucket = aws_s3_bucket.bucket[each.key].id
  rule {
    id = "Delete old files"
    expiration {
      days = each.value.expiration_days
    }
    noncurrent_version_expiration {
      noncurrent_days = each.value.expiration_days
    }
    filter {}
    status = "Enabled"
  }
  rule {
    id = "Delete deletion markers"
    expiration {
      expired_object_delete_marker = true
    }
    noncurrent_version_expiration {
      noncurrent_days = each.value.expiration_days
    }
    filter {}
    status = "Enabled"
  }

}

resource "aws_s3_bucket_cors_configuration" "media" {
  bucket = aws_s3_bucket.bucket["media"].id
  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET", "PUT", "POST", "HEAD"]
    allowed_origins = [
      "https://ascii-art-aws.vercel.app" // TODO: replace with valid origins
    ]
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
