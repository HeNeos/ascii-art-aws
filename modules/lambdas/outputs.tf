output "lambda_function_arn" {
  description = "The ARN of the Lambda function"
  value       = aws_lambda_function.lambda_function.arn
}

output "lambda_function_name" {
  description = "The name of the Lambda function"
  value       = aws_lambda_function.lambda_function.function_name
}
