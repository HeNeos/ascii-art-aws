resource "aws_s3_bucket" "test-bucket" {
  bucket = "test-s3-bucket-ascii-art-123456"
  tags = {
    Name        = "test-s3-bucket-ascii-art"
    Environment = "Dev"
  }
}
