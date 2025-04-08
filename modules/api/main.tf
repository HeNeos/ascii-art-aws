resource "aws_api_gateway_rest_api" "ascii_api" {
  name = "ascii-api"
}

resource "aws_api_gateway_resource" "upload" {
  rest_api_id = aws_api_gateway_rest_api.ascii_api.id
  parent_id   = aws_api_gateway_rest_api.ascii_api.root_resource_id
  path_part   = "generate-upload-url"
}

resource "aws_api_gateway_method" "upload_method" {
  rest_api_id   = aws_api_gateway_rest_api.ascii_api.id
  resource_id   = aws_api_gateway_resource.upload.id
  http_method   = "POST"
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
  source_file = "lambda_function.py"
  output_path = "lambda_function_payload.zip"
}


resource "aws_lambda_function" "upload_lambda" {
  function_name    = "upload_lambda-${var.stage}"
  handler          = "lambda_function.lambda_handler"
  runtime          = "python3.12"
  role             = aws_iam_role.upload_lambda.arn
  source_code_hash = data.archive_file.upload_lambda.output_base64sha256
  filename         = data.archive_file.upload_lambda.output_path
  timeout          = 5

  environment {
    variables = {
      UPLOAD_BUCKET = var.media_bucket_name
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

resource "aws_lambda_permission" "apigw_lambda" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.upload_lambda.function_name
  principal     = "apigateway.amazonaws.com"

  source_arn = "arn:aws:execute-api:${var.region}:${var.account_id}:${aws_api_gateway_rest_api.ascii_api.id}/*/${aws_api_gateway_method.upload_method.http_method}${aws_api_gateway_resource.upload.path}"
}
