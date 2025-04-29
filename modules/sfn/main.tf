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
    effect = "Allow"

    principals {
      identifiers = ["states.amazonaws.com", "events.amazonaws.com"]
      type        = "Service"
    }
    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "lambda_role" {
  name               = "lambda-role-${var.stage}"
  assume_role_policy = data.aws_iam_policy_document.lambda_policy_assume_role.json
}

resource "aws_iam_policy" "bucket" {
  name = "bucket-policy-${var.stage}"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow",
        Action = ["s3:Get*", "s3:List*", "s3:Describe*"],
        Resource = [
          "${var.media_bucket_arn}",
          "${var.media_bucket_arn}/*",
          "${var.audio_bucket_arn}",
          "${var.audio_bucket_arn}/*",
          "${var.ascii_art_bucket_arn}",
          "${var.ascii_art_bucket_arn}/*",
          "${var.r2_secrets_bucket_arn}",
          "${var.r2_secrets_bucket_arn}/*"
        ]
      },
      {
        Effect   = "Allow",
        Action   = ["s3:Put*"],
        Resource = ["${var.media_bucket_arn}/*", "${var.ascii_art_bucket_arn}/*", "${var.audio_bucket_arn}/*"]
      }
    ]
  })
}

resource "aws_iam_policy" "dynamo" {
  name = "status-table-policy-${var.stage}"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "dynamodb:GetItem",
          "dynamodb:Query",
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
        ]
        Resource = [var.status_table_arn]
      }
    ]
  })
}

resource "aws_iam_policy_attachment" "lambda_exec_attachment" {
  name       = "lambda-execution-policy-${var.stage}"
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  roles      = [aws_iam_role.lambda_role.name]
}

resource "aws_iam_policy_attachment" "attach_bucket_policy" {
  name       = "lambda-bucket-policy-${var.stage}"
  policy_arn = aws_iam_policy.bucket.arn
  roles      = [aws_iam_role.lambda_role.name]
}

resource "aws_iam_policy_attachment" "attach_status_table_policy" {
  name       = "lambda-status-table-policy-${var.stage}"
  policy_arn = aws_iam_policy.dynamo.arn
  roles      = [aws_iam_role.lambda_role.name]
}

resource "aws_iam_role" "step_function_role" {
  name               = "step-function-role-${var.stage}"
  assume_role_policy = data.aws_iam_policy_document.step_function_policy_assume_role.json
}

resource "aws_iam_role_policy" "step_function_policy" {
  name   = "step-function-role-policy-${var.stage}"
  role   = aws_iam_role.step_function_role.id
  policy = <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Action": "states:StartExecution",
      "Effect": "Allow",
      "Resource": "${aws_sfn_state_machine.step_function.arn}"
    }
  ]
}
EOF
}

resource "aws_iam_policy_attachment" "step_function_lambda_attachment" {
  name       = "step-function-lambda-policy-${var.stage}"
  roles      = [aws_iam_role.step_function_role.name]
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaRole"
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
  timeout       = 30
  memory_size   = 3009
  architectures = ["arm64"]
  ephemeral_storage {
    size = 512
  }

  environment {
    variables = {
      MEDIA_BUCKET      = var.media_bucket_name
      STATUS_TABLE_NAME = var.status_table_name
      MAX_HEIGHT        = "2880"
    }
  }
}

resource "aws_lambda_permission" "allow_bucket" {
  statement_id  = "AllowExecutionFromS3Bucket-${var.stage}"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.downsize_media.arn
  principal     = "s3.amazonaws.com"
  source_arn    = var.media_bucket_arn
}

resource "aws_s3_bucket_notification" "media_bucket_notification" {
  bucket      = var.media_bucket_name
  eventbridge = true
}

resource "aws_cloudwatch_event_rule" "trigger_rule" {
  name = "s3-object-created-rule-${var.stage}"
  event_pattern = jsonencode({
    "source" : ["aws.s3"],
    "detail-type" : ["Object Created"],
    "detail" = {
      "bucket" = {
        "name" = [var.media_bucket_name]
      },
      "object" = {
        "key" = [{
          "prefix" = "raw/"
        }]
      }
    }
  })
}

resource "aws_cloudwatch_event_target" "trigger_target" {
  rule     = aws_cloudwatch_event_rule.trigger_rule.name
  arn      = aws_sfn_state_machine.step_function.arn
  role_arn = aws_iam_role.step_function_role.arn
}

resource "aws_lambda_function" "downsize_video" {
  function_name = var.lambda_function_name_downsize_video
  role          = aws_iam_role.lambda_role.arn
  package_type  = "Image"
  image_uri     = "${var.lambda_image_downsize_video}:latest"
  timeout       = 60
  memory_size   = 7076
  architectures = ["arm64"]
  ephemeral_storage {
    size = 1024
  }

  environment {
    variables = {
      MEDIA_BUCKET      = var.media_bucket_name
      STATUS_TABLE_NAME = var.status_table_name
      MAX_HEIGHT        = "1080"
    }
  }
}

resource "aws_lambda_function" "extract_audio" {
  function_name = var.lambda_function_name_extract_audio
  role          = aws_iam_role.lambda_role.arn
  package_type  = "Image"
  image_uri     = "${var.lambda_image_extract_audio}:latest"
  timeout       = 40
  memory_size   = 1024
  architectures = ["arm64"]

  environment {
    variables = {
      AUDIO_BUCKET = var.audio_bucket_name
      MEDIA_BUCKET = var.media_bucket_name
    }
  }
}

resource "aws_lambda_function" "merge_frames" {
  function_name = var.lambda_function_name_merge_frames
  role          = aws_iam_role.lambda_role.arn
  package_type  = "Image"
  image_uri     = "${var.lambda_image_merge_frames}:latest"
  timeout       = 180
  memory_size   = 8845
  architectures = ["arm64"]

  ephemeral_storage {
    size = 2048
  }

  environment {
    variables = {
      ASCII_ART_BUCKET  = var.ascii_art_bucket_name
      MEDIA_BUCKET      = var.media_bucket_name
      AUDIO_BUCKET      = var.audio_bucket_name
      R2_SECRETS_BUCKET = var.r2_secrets_bucket_name
      STATUS_TABLE_NAME = var.status_table_name
    }
  }
}

resource "aws_lambda_function" "process_frames" {
  function_name = var.lambda_function_name_process_frames
  role          = aws_iam_role.lambda_role.arn
  package_type  = "Image"
  image_uri     = "${var.lambda_image_process_frames}:latest"
  timeout       = 150
  memory_size   = 5308
  architectures = ["arm64"]
  ephemeral_storage {
    size = 1024
  }
  environment {
    variables = {
      ASCII_ART_BUCKET  = var.ascii_art_bucket_name
      MEDIA_BUCKET      = var.media_bucket_name
      R2_SECRETS_BUCKET = var.r2_secrets_bucket_name
      NUMBA_CACHE_DIR   = "/tmp/__pycache__/"
      DEFAULT_DITHERING = "atkinson"
      STATUS_TABLE_NAME = var.status_table_name
    }
  }
}

resource "aws_lambda_function" "process_image" {
  function_name = var.lambda_function_name_process_image
  role          = aws_iam_role.lambda_role.arn
  package_type  = "Image"
  image_uri     = "${var.lambda_image_process_image}:latest"
  timeout       = 60
  memory_size   = 5308
  architectures = ["arm64"]
  ephemeral_storage {
    size = 1024
  }
  environment {
    variables = {
      ASCII_ART_BUCKET  = var.ascii_art_bucket_name
      MEDIA_BUCKET      = var.media_bucket_name
      R2_SECRETS_BUCKET = var.r2_secrets_bucket_name
      NUMBA_CACHE_DIR   = "/tmp/__pycache__/"
      DEFAULT_DITHERING = "atkinson"
      STATUS_TABLE_NAME = var.status_table_name
    }
  }
}

resource "aws_cloudwatch_log_group" "lambdas_log_group" {
  for_each = tomap({
    "downsize_media" = aws_lambda_function.downsize_media.function_name
    "downsize_video" = aws_lambda_function.downsize_video.function_name
    "extract_audio"  = aws_lambda_function.extract_audio.function_name
    "merge_frames"   = aws_lambda_function.merge_frames.function_name
    "process_frames" = aws_lambda_function.process_frames.function_name
    "process_image"  = aws_lambda_function.process_image.function_name
  })
  name              = "/aws/lambda/${each.value}"
  retention_in_days = 7
}


resource "aws_cloudwatch_log_group" "sfn_log_group" {
  name              = "/aws/vendedlogs/states/AsciiArt-${var.stage}-Logs"
  retention_in_days = 7
  tags = {
    Environment = var.stage
    Project     = "AsciiArt"
  }
}

resource "aws_iam_role_policy" "sfn_logging_policy" {
  name = "StepFunctionLoggingPolicy-${var.stage}"
  role = aws_iam_role.step_function_role.id
  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Action = [
          "logs:CreateLogDelivery",
          "logs:GetLogDelivery",
          "logs:UpdateLogDelivery",
          "logs:DeleteLogDelivery",
          "logs:ListLogDeliveries",
          "logs:PutResourcePolicy",
          "logs:DescribeResourcePolicies",
          "logs:DescribeLogGroups"
        ],
        Resource = "*"
      },
      {
        Effect = "Allow",
        Action = [
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ],
        Resource = "${aws_cloudwatch_log_group.sfn_log_group.arn}:*"
      }
    ]
  })
}

resource "aws_cloudwatch_log_resource_policy" "sfn_log_policy" {
  policy_name = "AsciiArt-StepFunction-Logs-${var.stage}"
  policy_document = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Principal = {
          Service = "states.amazonaws.com"
        },
        Action = [
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ],
        Resource = "${aws_cloudwatch_log_group.sfn_log_group.arn}:*"
      }
    ]
  })
}


resource "aws_sfn_state_machine" "step_function" {
  name     = "AsciiArt-${var.stage}"
  role_arn = aws_iam_role.step_function_role.arn
  type     = "EXPRESS"

  logging_configuration {
    log_destination        = "${aws_cloudwatch_log_group.sfn_log_group.arn}:*"
    include_execution_data = true
    level                  = "ALL"
  }

  definition = <<-DEFINITION
  {
    "Comment": "AsciiArt State Machine",
    "StartAt": "ExtractFileExtension",
    "States": {
      "ExtractFileExtension": {
        "Type": "Pass",
        "ResultPath": "$.extractedData",
        "Parameters": {
          "key.$": "$.detail.object.key",
          "bucket_name.$": "$.detail.bucket.name",
          "extension.$": "States.ArrayGetItem(States.StringSplit($.detail.object.key, '.'), States.MathAdd(States.ArrayLength(States.StringSplit($.detail.object.key, '.')), -1))"
        },
        "Next": "CheckExtension"
      },
      "CheckExtension": {
        "Type": "Choice",
        "Choices": [
          {
            "Variable": "$.extractedData.extension",
            "StringEquals": "mp4",
            "Next": "PrepareVideoOutput"
          },
          {
            "Variable": "$.extractedData.extension",
            "StringEquals": "MP4",
            "Next": "PrepareVideoOutput"
          },
          {
            "Variable": "$.extractedData.extension",
            "StringEquals": "mov",
            "Next": "PrepareVideoOutput"
          },
          {
            "Variable": "$.extractedData.extension",
            "StringEquals": "avi",
            "Next": "PrepareVideoOutput"
          },
          {
            "Variable": "$.extractedData.extension",
            "StringEquals": "jpg",
            "Next": "PrepareImageOutput"
          },
          {
            "Variable": "$.extractedData.extension",
            "StringEquals": "JPG",
            "Next": "PrepareImageOutput"
          },
          {
            "Variable": "$.extractedData.extension",
            "StringEquals": "png",
            "Next": "PrepareImageOutput"
          },
          {
            "Variable": "$.extractedData.extension",
            "StringEquals": "PNG",
            "Next": "PrepareImageOutput"
          },
          {
            "Variable": "$.extractedData.extension",
            "StringEquals": "jpeg",
            "Next": "PrepareImageOutput"
          },
          {
            "Variable": "$.extractedData.extension",
            "StringEquals": "JPEG",
            "Next": "PrepareImageOutput"
          }
        ],
        "Default": "NotSupported"
      },
      "PrepareVideoOutput": {
        "Type": "Pass",
        "ResultPath": "$",
        "Parameters": {
          "bucket_name.$": "$.extractedData.bucket_name",
          "key.$": "$.extractedData.key",
          "is_video": true,
          "is_image": false
        },
        "Next": "DownsizeVideo"
      },
      "PrepareImageOutput": {
        "Type": "Pass",
        "ResultPath": "$",
        "Parameters": {
          "bucket_name.$": "$.extractedData.bucket_name",
          "key.$": "$.extractedData.key",
          "is_video": false,
          "is_image": true
        },
        "Next": "DownsizeMedia"
      },
      "NotSupported": {
        "Type": "Fail",
        "Error": "UnsupportedFormatError",
        "Cause": "The uploaded file format is not supported."
      },
      "DownsizeMedia": {
        "Type": "Task",
        "Resource": "${aws_lambda_function.downsize_media.arn}",
        "Next": "ProcessImage"
      },
      "DownsizeVideo": {
        "Type": "Task",
        "Resource": "${aws_lambda_function.downsize_video.arn}",
        "Next": "ProcessVideo"
      },
      "ProcessVideo": {
        "Type": "Parallel",
        "Branches": [
          {
            "StartAt": "ExtractAudio",
            "States": {
              "ExtractAudio": {
                "Type": "Task",
                "Resource": "${aws_lambda_function.extract_audio.arn}",
                "End": true
              }
            }
          },
          {
            "StartAt": "MapProcessFrames",
            "States": {
              "MapProcessFrames": {
                "Type": "Map",
                "ItemsPath": "$.processed_key",
                "Parameters": {
                  "key.$": "$.key",
                  "random_id.$": "$.random_id",
                  "is_video.$": "$.is_video",
                  "is_image.$": "$.is_image",
                  "processed_key.$": "$$.Map.Item.Value"
                },
                "ItemProcessor": {
                  "ProcessorConfig": {
                    "Mode": "INLINE"
                  },
                  "StartAt": "ProcessFrame",
                  "States": {
                    "ProcessFrame": {
                      "Type": "Task",
                      "Resource": "arn:aws:states:::lambda:invoke",
                      "Parameters": {
                        "Payload.$": "$",
                        "FunctionName": "${aws_lambda_function.process_frames.arn}"
                      },
                      "ResultSelector": {
                        "processed_frame.$": "$.Payload.ascii_art_key"
                      },
                      "ResultPath": "$.processed_frame_result",
                      "End": true
                    }
                  }
                },
                "ResultSelector": {
                  "videos_key.$": "$[*].processed_frame_result.processed_frame"
                },
                "End": true
              }
            }
          }
        ],
        "ResultPath": "$.parallelResult",
        "Next": "MergeFrames"
      },
      "ProcessImage": {
        "Type": "Task",
        "Resource": "${aws_lambda_function.process_image.arn}",
        "End": true
      },
      "MergeFrames": {
        "Type": "Task",
        "Resource": "${aws_lambda_function.merge_frames.arn}",
        "Parameters": {
          "audio_key.$": "$.parallelResult[0].audio_key",
          "key.$": "$.parallelResult[0].key",
          "random_id.$": "$.parallelResult[0].random_id",
          "videos_key.$": "$.parallelResult[1].videos_key"
        },
        "End": true
      }
    }
  }
  DEFINITION
}

