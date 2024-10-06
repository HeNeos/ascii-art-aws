data "aws_iam_policy_document" "lambda_policy_assume_role" {
  statement {
    sid    = ""
    effect = "Allow"

    principals {
      identifiers = ["lambda.amazonaws.com"]
      type        = "Service"
    }
    actions = ["sts:AssumeRole"]
  }
}

data "aws_iam_policy_document" "step_function_policy_assume_role" {
  statement {
    sid    = ""
    effect = "Allow"

    principals {
      identifiers = ["states.amazonaws.com"]
      type        = "Service"
    }
    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "lambda_role" {
  name               = "lambda-role-${var.stage}"
  assume_role_policy = data.aws_iam_policy_document.lambda_policy_assume_role.json
}

resource "aws_iam_policy_attachment" "lambda_exec_attachment" {
  name       = "lambda-execution-policy-${var.stage}"
  roles      = [aws_iam_role.lambda_role.name]
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role" "step_function_role" {
  name               = "ste-function-role-${var.stage}"
  assume_role_policy = data.aws_iam_policy_document.step_function_policy_assume_role.json
}

resource "aws_iam_policy_attachment" "step_function_attachment" {
  name       = "step-function-policy-${var.stage}"
  roles      = [aws_iam_role.step_function_role.name]
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSStepFunctionsFullAccess"
}

resource "aws_lambda_function" "downsize_media" {
  function_name = var.lambda_function_name_downsize_media
  role          = aws_iam_role.lambda_role.arn
  package_type  = "Image"
  image_uri     = "${var.lambda_image_downsize_media}:latest"
  timeout       = 60
}

resource "aws_lambda_function" "extract_audio" {
  function_name = var.lambda_function_name_extract_audio
  role          = aws_iam_role.lambda_role.arn
  package_type  = "Image"
  image_uri     = "${var.lambda_image_extract_audio}:latest"
  timeout       = 60
}

resource "aws_lambda_function" "merge_frames" {
  function_name = var.lambda_function_name_merge_frames
  role          = aws_iam_role.lambda_role.arn
  package_type  = "Image"
  image_uri     = "${var.lambda_image_merge_frames}:latest"
  timeout       = 60
}

resource "aws_lambda_function" "proccess_frames" {
  function_name = var.lambda_function_name_proccess_frames
  role          = aws_iam_role.lambda_role.arn
  package_type  = "Image"
  image_uri     = "${var.lambda_image_proccess_frames}:latest"
  timeout       = 60
}


resource "aws_lambda_function" "split_frames" {
  function_name = var.lambda_function_name_split_frames
  role          = aws_iam_role.lambda_role.arn
  package_type  = "Image"
  image_uri     = "${var.lambda_image_split_frames}:latest"
  timeout       = 60
}

resource "aws_sfn_state_machine" "step_function" {
  name     = "AsciiArt-${var.stage}"
  role_arn = aws_iam_role.step_function_role.arn

  definition = <<-DEFINITION
  {
    "Comment": "My Lambda Orchestration",
    "StartAt": "FirstLambda",
    "States": {
      "FirstLambda": {
        "Type": "Task",
        "Resource": "${aws_lambda_function.downsize_media.arn}",
        "Next": "SecondLambda"
      },
      "SecondLambda": {
        "Type": "Task",
        "Resource": "${aws_lambda_function.extract_audio.arn}",
        "End": true
      }
    }
  }
  DEFINITION
}
