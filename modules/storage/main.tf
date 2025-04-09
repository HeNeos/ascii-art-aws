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
      "*" // TODO: fix it
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
    allowed_methods = ["GET", "PUT", "POST", "HEAD"]
    allowed_origins = [
      "*" // TODO: fix it
    ]
    expose_headers  = ["ETag"]
    max_age_seconds = 3000
  }
}
