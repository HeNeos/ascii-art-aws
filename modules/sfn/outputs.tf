output "lambda_arn_downsize_media" {
  description = "The ARN of the Lambda function"
  value       = aws_lambda_function.downsize_media.arn
}

output "lambda_arn_split_frames" {
  value = aws_lambda_function.split_frames.arn
}
