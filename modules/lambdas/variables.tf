variable "function_name" {
  description = "The name of the Lambda function"
  type        = string
  default     = "test-lambda-function"
}

variable "handler" {
  description = "The function within your code to call (e.g. 'lambda_function.lambda_handler')"
  type        = string
  default     = "lambda_handler"
}

variable "runtime" {
  description = "The runtime for the Lambda function (e.g., python3.9)"
  type        = string
  default     = "python3.12"
}

variable "environment_variables" {
  description = "Environment variables to pass to the Lambda function"
  type        = map(string)
  default     = {}
}

variable "timeout" {
  description = "The amount of time (in seconds) Lambda allows a function to run"
  type        = number
  default     = 15
}

variable "memory_size" {
  description = "Amount of memory in MB your Lambda function can use at runtime"
  type        = number
  default     = 128
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "stage" {
  description = "Deployment stage (e.g., dev, prod)"
  type        = string
  default     = "dev"
}
