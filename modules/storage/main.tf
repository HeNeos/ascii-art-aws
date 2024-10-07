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

resource "aws_s3_bucket" "ascii_art" {
  bucket = "ascii-art-bucket-${var.stage}-${var.account_id}"

  lifecycle {
    prevent_destroy = true
  }
}
