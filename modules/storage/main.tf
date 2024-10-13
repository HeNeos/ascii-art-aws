resource "aws_s3_bucket" "media" {
  bucket = "media-bucket-${var.stage}-${var.account_id}"

  lifecycle {
    prevent_destroy = true
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
      days = 5
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
      days = 5
    }
    status = "Enabled"
  }
}
