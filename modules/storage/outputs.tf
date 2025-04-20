output "media_bucket_name" {
  value = aws_s3_bucket.bucket["media"].id
}

output "audio_bucket_name" {
  value = aws_s3_bucket.bucket["audio"].id
}

output "ascii_art_bucket_name" {
  value = aws_s3_bucket.bucket["ascii_art"].id
}

output "media_bucket_arn" {
  value = aws_s3_bucket.bucket["media"].arn
}

output "audio_bucket_arn" {
  value = aws_s3_bucket.bucket["audio"].arn
}

output "ascii_art_bucket_arn" {
  value = aws_s3_bucket.bucket["ascii_art"].arn
}

output "r2_secrets_bucket_name" {
  value = aws_s3_bucket.r2_secrets.id
}

output "r2_secrets_bucket_arn" {
  value = aws_s3_bucket.r2_secrets.arn
}
