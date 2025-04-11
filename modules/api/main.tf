resource "aws_api_gateway_rest_api" "ascii_api" {
  name = "ascii-api"
}

resource "aws_api_gateway_resource" "upload" {
  rest_api_id = aws_api_gateway_rest_api.ascii_api.id
  parent_id   = aws_api_gateway_rest_api.ascii_api.root_resource_id
  path_part   = "generate-upload-url"
}

resource "aws_api_gateway_resource" "poll" {
  rest_api_id = aws_api_gateway_rest_api.ascii_api.id
  parent_id   = aws_api_gateway_rest_api.ascii_api.root_resource_id
  path_part   = "poll-ascii-art"
}

resource "aws_api_gateway_method" "upload_method" {
  rest_api_id   = aws_api_gateway_rest_api.ascii_api.id
  resource_id   = aws_api_gateway_resource.upload.id
  http_method   = "POST"
  authorization = "NONE"
}

resource "aws_api_gateway_method" "poll_method" {
  rest_api_id   = aws_api_gateway_rest_api.ascii_api.id
  resource_id   = aws_api_gateway_resource.poll.id
  http_method   = "GET"
  authorization = "NONE"
}


data "aws_iam_policy_document" "upload_lambda_assume_role_policy" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_policy" "upload_lambda_policy" {
  name = "upload_lambda_policy-${var.stage}"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:PutObject",
          "s3:PutObjectAcl",
        ]
        Resource = "${var.media_bucket_arn}/*"
      },
      {
        Effect   = "Allow"
        Action   = ["logs:*"]
        Resource = "*"
      },
      {
        Effect   = "Allow"
        Action   = ["dynamodb:PutItem"]
        Resource = aws_dynamodb_table.ascii_art.arn
      },
    ]
  })
}

resource "aws_iam_role" "upload_lambda" {
  name               = "upload_lambda_role-${var.stage}"
  assume_role_policy = data.aws_iam_policy_document.upload_lambda_assume_role_policy.json
}

resource "aws_iam_policy_attachment" "upload_lambda_policy_attachment" {
  name       = "upload_lambda_policy_attachment-${var.stage}"
  roles      = [aws_iam_role.upload_lambda.name]
  policy_arn = aws_iam_policy.upload_lambda_policy.arn
}

data "archive_file" "upload_lambda" {
  type        = "zip"
  source_file = "${path.module}/upload_lambda.py"
  output_path = "${path.module}/upload_lambda_payload.zip"
}


resource "aws_lambda_function" "upload_lambda" {
  function_name    = "upload_lambda-${var.stage}"
  handler          = "upload_lambda.lambda_handler"
  runtime          = "python3.12"
  role             = aws_iam_role.upload_lambda.arn
  source_code_hash = data.archive_file.upload_lambda.output_base64sha256
  filename         = data.archive_file.upload_lambda.output_path
  timeout          = 5

  environment {
    variables = {
      UPLOAD_BUCKET     = var.media_bucket_name
      STATUS_TABLE_NAME = aws_dynamodb_table.ascii_art.name
    }
  }
}

resource "aws_api_gateway_integration" "upload_lambda" {
  rest_api_id             = aws_api_gateway_rest_api.ascii_api.id
  resource_id             = aws_api_gateway_resource.upload.id
  http_method             = aws_api_gateway_method.upload_method.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.upload_lambda.invoke_arn
}

resource "aws_lambda_permission" "apigw_upload_lambda" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.upload_lambda.function_name
  principal     = "apigateway.amazonaws.com"

  source_arn = "arn:aws:execute-api:${var.region}:${var.account_id}:${aws_api_gateway_rest_api.ascii_api.id}/*/${aws_api_gateway_method.upload_method.http_method}${aws_api_gateway_resource.upload.path}"
}

resource "aws_dynamodb_table" "ascii_art" {
  name           = "ascii_art_status-${var.stage}"
  billing_mode   = "PROVISIONED"
  write_capacity = 20
  read_capacity  = 20

  hash_key  = "status"
  range_key = "id"

  attribute {
    name = "status"
    type = "S"
  }

  attribute {
    name = "id"
    type = "S"
  }

  ttl {
    enabled        = true
    attribute_name = "ttl"
  }
}

data "aws_iam_policy_document" "poll_lambda_assume_role_policy" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_policy" "poll_lambda_policy" {
  name = "poll_lambda_policy-${var.stage}"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:GetItem",
          "dynamodb:Query",
        ]
        Resource = aws_dynamodb_table.ascii_art.arn
      },
      {
        Effect   = "Allow"
        Action   = ["logs:*"]
        Resource = "*"
      },
    ]
  })
}

resource "aws_iam_role" "poll_lambda" {
  name               = "poll_lambda_role-${var.stage}"
  assume_role_policy = data.aws_iam_policy_document.poll_lambda_assume_role_policy.json
}

resource "aws_iam_policy_attachment" "poll_lambda_policy_attachment" {
  name       = "poll_lambda_policy_attachment-${var.stage}"
  roles      = [aws_iam_role.poll_lambda.name]
  policy_arn = aws_iam_policy.poll_lambda_policy.arn
}

data "archive_file" "poll_lambda" {
  type        = "zip"
  source_file = "${path.module}/poll_lambda.py"
  output_path = "${path.module}/poll_lambda_payload.zip"
}

resource "aws_lambda_function" "poll_lambda" {
  function_name    = "poll_lambda-${var.stage}"
  handler          = "poll_lambda.lambda_handler"
  runtime          = "python3.12"
  role             = aws_iam_role.poll_lambda.arn
  source_code_hash = data.archive_file.poll_lambda.output_base64sha256
  filename         = data.archive_file.poll_lambda.output_path
  timeout          = 5

  environment {
    variables = {
      STATUS_TABLE_NAME = aws_dynamodb_table.ascii_art.name
    }
  }
}


resource "aws_api_gateway_integration" "poll_lambda" {
  rest_api_id             = aws_api_gateway_rest_api.ascii_api.id
  resource_id             = aws_api_gateway_resource.poll.id
  http_method             = aws_api_gateway_method.poll_method.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.poll_lambda.invoke_arn
}

resource "aws_lambda_permission" "apigw_poll_lambda" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.poll_lambda.function_name
  principal     = "apigateway.amazonaws.com"

  source_arn = "arn:aws:execute-api:${var.region}:${var.account_id}:${aws_api_gateway_rest_api.ascii_api.id}/*/${aws_api_gateway_method.poll_method.http_method}${aws_api_gateway_resource.poll.path}"
}

resource "aws_api_gateway_deployment" "ascii_api" {
  rest_api_id = aws_api_gateway_rest_api.ascii_api.id
  depends_on = [
    aws_api_gateway_method.upload_method,
    aws_api_gateway_method.poll_method,
    aws_api_gateway_integration.upload_lambda,
    aws_api_gateway_integration.poll_lambda
  ]
}

resource "aws_api_gateway_stage" "ascii_api" {
  stage_name    = var.stage
  rest_api_id   = aws_api_gateway_rest_api.ascii_api.id
  deployment_id = aws_api_gateway_deployment.ascii_api.id
}

resource "aws_api_gateway_method_settings" "upload_settings" {
  rest_api_id = aws_api_gateway_rest_api.ascii_api.id
  stage_name  = aws_api_gateway_stage.ascii_api.stage_name
  method_path = "${aws_api_gateway_resource.upload.path_part}/POST"

  settings {
    throttling_burst_limit = 20
    throttling_rate_limit  = 10
    caching_enabled        = true
    cache_ttl_in_seconds   = 600
  }
}

resource "aws_api_gateway_method_settings" "poll_settings" {
  rest_api_id = aws_api_gateway_rest_api.ascii_api.id
  stage_name  = aws_api_gateway_stage.ascii_api.stage_name
  method_path = "${aws_api_gateway_resource.poll.path_part}/GET"

  settings {
    throttling_burst_limit = 20
    throttling_rate_limit  = 10
    caching_enabled        = true
    cache_ttl_in_seconds   = 600
  }
}

resource "aws_cloudwatch_log_group" "lambdas_log_group" {
  for_each = tomap({
    "poll_lambda"   = aws_lambda_function.poll_lambda.function_name
    "upload_lambda" = aws_lambda_function.upload_lambda.function_name
  })
  name              = "/aws/lambda/${each.value}"
  retention_in_days = 7
}
