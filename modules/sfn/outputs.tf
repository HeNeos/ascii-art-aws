output "lambda_arn_downsize_media" {
  description = "The ARN of the Lambda function"
  value       = aws_lambda_function.downsize_media.arn
}

output "step_function_arn" {
  description = "The ARN of the Step Function"
  value       = aws_sfn_state_machine.step_function.arn
}
