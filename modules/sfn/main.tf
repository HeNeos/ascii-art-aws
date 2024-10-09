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

resource "aws_iam_policy" "media_bucket" {
  name = "media-bucket-policy-${var.stage}"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow",
        Action   = ["s3:Get*", "s3:List*", "s3:Describe*"],
        Resource = ["${var.media_bucket_arn}", "${var.media_bucket_arn}/*"]
      },
      {
        Effect   = "Allow",
        Action   = ["s3:Put*"],
        Resource = ["${var.media_bucket_arn}/*", "${var.ascii_art_bucket_arn}", "${var.audio_bucket_arn}"]
      }
    ]
  })
}

resource "aws_iam_policy_attachment" "lambda_exec_attachment" {
  name       = "lambda-execution-policy-${var.stage}"
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  roles      = [aws_iam_role.lambda_role.name]
}

resource "aws_iam_policy_attachment" "attach_media_bucket_policy" {
  name       = "lambda-media-bucket-policy-${var.stage}"
  policy_arn = aws_iam_policy.media_bucket.arn
  roles      = [aws_iam_role.lambda_role.name]
}

resource "aws_iam_role" "step_function_role" {
  name               = "step-function-role-${var.stage}"
  assume_role_policy = data.aws_iam_policy_document.step_function_policy_assume_role.json
}

resource "aws_iam_policy_attachment" "step_function_attachment" {
  name       = "step-function-policy-${var.stage}"
  roles      = [aws_iam_role.step_function_role.name]
  policy_arn = "arn:aws:iam::aws:policy/AWSStepFunctionsFullAccess"
}

resource "aws_lambda_function" "downsize_media" {
  function_name = var.lambda_function_name_downsize_media
  role          = aws_iam_role.lambda_role.arn
  package_type  = "Image"
  image_uri     = "${var.lambda_image_downsize_media}:latest"
  timeout       = 120
  memory_size   = 3008
  ephemeral_storage {
    size = 2048
  }
}

resource "aws_lambda_permission" "allow_bucket" {
  statement_id  = "AllowExecutionFromS3Bucket"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.downsize_media.arn
  principal     = "s3.amazonaws.com"
  source_arn    = var.media_bucket_arn
}

resource "aws_s3_bucket_notification" "media_bucket_notification" {
  bucket = var.media_bucket_name

  lambda_function {
    lambda_function_arn = aws_lambda_function.downsize_media.arn
    events              = ["s3:ObjectCreated:*"]

    filter_prefix = "raw/"
  }

  depends_on = [aws_lambda_permission.allow_bucket]
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
  memory_size   = 1024
  ephemeral_storage {
    size = 1024
  }
  environment {
    variables = {
      ASCII_ART_BUCKET = var.ascii_art_bucket_name
    }
  }
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
