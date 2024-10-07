output "media_bucket_name" {
  value = aws_s3_bucket.media.id
}

output "audio_bucket_name" {
  value = aws_s3_bucket.audio.id
}

output "ascii_art_bucket_name" {
  value = aws_s3_bucket.ascii_art.id
}

output "media_bucket_arn" {
  value = aws_s3_bucket.media.arn
}

output "audio_bucket_arn" {
  value = aws_s3_bucket.audio.arn
}

output "ascii_art_bucket_arn" {
  value = aws_s3_bucket.ascii_art.arn
}
