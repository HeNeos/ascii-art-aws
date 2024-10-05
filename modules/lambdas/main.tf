resource "aws_iam_role" "test_lambda_role" {
  name               = "${var.function_name}-role"
  assume_role_policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "sts:AssumeRole",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Effect": "Allow"
    }
  ]
}
EOF
}

resource "aws_iam_role_policy" "test_lambda_policy" {
  name   = "${var.function_name}-policy"
  role   = aws_iam_role.test_lambda_role.id
  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    }
  ]
}
EOF
}

resource "aws_lambda_function" "test_lambda_function" {
  function_name = var.function_name
  role          = aws_iam_role.test_lambda_role.arn
  handler       = var.handler
  runtime       = var.runtime

  source_code_hash = filebase64sha256("./lambda_function.py")
  filename         = "./lambda_function.py"

  # environment {
  #   variables = var.environment_variables
  # }

  timeout     = var.timeout
  memory_size = var.memory_size

  tags = {
    Environment = var.stage
  }
}

# resource "aws_cloudwatch_log_group" "lambda_log_group" {
#   name              = "/aws/lambda/${var.function_name}"
#   retention_in_days = 14
# }
