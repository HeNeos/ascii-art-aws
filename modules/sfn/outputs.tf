output "lambda_arn_downsize_media" {
  description = "The ARN of the Lambda function"
  value       = aws_lambda_function.downsize_media.arn
}

output "lambda_arn_downsize_video" {
  description = "The ARN of the Lambda function"
  value       = aws_lambda_function.downsize_video.arn
}

output "lambda_arn_extract_audio" {
  description = "The ARN of the Lambda function"
  value       = aws_lambda_function.extract_audio.arn
}

output "lambda_arn_merge_frames" {
  description = "The ARN of the Lambda function"
  value       = aws_lambda_function.merge_frames.arn
}

output "lambda_arn_process_frames" {
  description = "The ARN of the Lambda function"
  value       = aws_lambda_function.process_frames.arn
}

output "lambda_arn_process_image" {
  description = "The ARN of the Lambda function"
  value       = aws_lambda_function.process_image.arn
}

output "step_function_arn" {
  description = "The ARN of the Step Function"
  value       = aws_sfn_state_machine.step_function.arn
}
