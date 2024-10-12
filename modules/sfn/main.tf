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
        Resource = ["${var.media_bucket_arn}", "${var.media_bucket_arn}/*", "${var.audio_bucket_arn}", "${var.audio_bucket_arn}/*", "${var.ascii_art_bucket_arn}", "${var.ascii_art_bucket_arn}/*"]
      },
      {
        Effect   = "Allow",
        Action   = ["s3:Put*"],
        Resource = ["${var.media_bucket_arn}/*", "${var.ascii_art_bucket_arn}/*", "${var.audio_bucket_arn}/*"]
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
  memory_size   = 3008
  ephemeral_storage {
    size = 1024
  }

  environment {
    variables = {
      MEDIA_BUCKET = var.media_bucket_name
    }
  }
}

resource "aws_lambda_function" "downsize_video" {
  function_name = var.lambda_function_name_downsize_video
  role          = aws_iam_role.lambda_role.arn
  package_type  = "Image"
  image_uri     = "${var.lambda_image_downsize_video}:latest"
  timeout       = 180
  memory_size   = 3008
  ephemeral_storage {
    size = 4096
  }

  environment {
    variables = {
      MEDIA_BUCKET = var.media_bucket_name
    }
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
  memory_size   = 3008

  ephemeral_storage {
    size = 4096
  }

  environment {
    variables = {
      ASCII_ART_BUCKET = var.ascii_art_bucket_name
      MEDIA_BUCKET     = var.media_bucket_name
      AUDIO_BUCKET     = var.audio_bucket_name
    }
  }
}

resource "aws_lambda_function" "process_frames" {
  function_name = var.lambda_function_name_process_frames
  role          = aws_iam_role.lambda_role.arn
  package_type  = "Image"
  image_uri     = "${var.lambda_image_process_frames}:latest"
  timeout       = 180
  memory_size   = 3008
  ephemeral_storage {
    size = 4096
  }
  environment {
    variables = {
      ASCII_ART_BUCKET = var.ascii_art_bucket_name
      MEDIA_BUCKET     = var.media_bucket_name
    }
  }
}


resource "aws_sfn_state_machine" "step_function" {
  name     = "AsciiArt-${var.stage}"
  role_arn = aws_iam_role.step_function_role.arn

  definition = <<-DEFINITION
  {
    "Comment": "AsciiArt State Machine",
    "StartAt": "IsVideo",
    "States": {
      "IsVideo": {
        "Type": "Choice",
        "Choices": [
          {
            "Variable": "$.is_video",
            "BooleanEquals": true,
            "Next": "DownsizeVideo"
          },
          {
            "Variable": "$.is_image",
            "BooleanEquals": true,
            "Next": "DownsizeMedia"
          }
        ]
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
                  "bucket_name.$": "$.bucket_name",
                  "is_video.$": "$.is_video",
                  "is_image.$": "$.is_image",
                  "processed_key.$": "$$.Map.Item.Value"
                },
                "ItemProcessor": {
                  "ProcessorConfig": {
                    "Mode": "DISTRIBUTED",
                    "ExecutionType": "EXPRESS"
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
        "Next": "CombineOutputs"
      },
      "ProcessImage": {
        "Type": "Task",
        "Resource": "${aws_lambda_function.process_frames.arn}",
        "End": true
      },
      "CombineOutputs": {
        "Type": "Pass",
        "Parameters": {
          "audio_key.$": "$[0].audio_key",
          "key.$": "$[0].key",
          "random_id.$": "$[0].random_id",
          "videos_key.$": "$[1].videos_key"
        },
        "Next": "MergeFrames"
      },
      "MergeFrames": {
        "Type": "Task",
        "Resource": "${aws_lambda_function.merge_frames.arn}",
        "End": true
      }
    }
  }
  DEFINITION
}
