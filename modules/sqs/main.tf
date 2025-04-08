# resource "aws_sqs_queue" "ascii_jobs" {
#   name = "ascii-processing-jobs"
# }

# resource "aws_sqs_queue_policy" "allow_sfn" {
#   queue_url = aws_sqs_queue.ascii_jobs.id

#   policy = jsonencode({
#     Version = "2012-10-17",
#     Statement = [
#       {
#         Effect    = "Allow",
#         Principal = { Service = "states.amazonaws.com" },
#         Action    = "sqs:ReceiveMessage",
#         Resource  = aws_sqs_queue.ascii_jobs.arn
#       }
#     ]
#   })
# }

# data "aws_iam_policy_document" "post_upload_assume_role_policy" {
#   statement {
#     effect  = "Allow"
#     actions = ["sts:AssumeRole"]
#     principals {
#       type        = "Service"
#       identifiers = ["lambda.amazonaws.com"]
#     }
#   }
# }

# resource "aws_iam_policy" "post_upload_policy" {
#   name = "post_upload_policy-${var.stage}"
#   policy = jsonencode({
#     Version = "2012-10-17"
#     Statement = [
#       {
#         Effect = "Allow"
#         Action = [
#           "s3:PutObject",
#           "s3:PutObjectAcl",
#         ]
#         Resource = "${var.media_bucket_arn}/*"
#       },
#       {
#         Effect   = "Allow"
#         Action   = ["logs:*"]
#         Resource = "*"
#       },
#     ]
#   })
# }

# resource "aws_iam_role" "post_upload" {
#   name               = "post_upload_role-${var.stage}"
#   assume_role_policy = data.aws_iam_policy_document.post_upload_assume_role_policy.json
# }

# resource "aws_iam_policy_attachment" "post_upload_policy_attachment" {
#   name       = "post_upload_policy_attachment-${var.stage}"
#   roles      = [aws_iam_role.post_upload.name]
#   policy_arn = aws_iam_policy.post_upload_policy.arn
# }

# data "archive_file" "post_upload" {
#   type        = "zip"
#   source_file = "lambda_function.py"
#   output_path = "lambda_function_payload.zip"
# }

# resource "aws_lambda_function" "post_upload" {
#   function_name    = "post_upload-${var.stage}"
#   runtime          = "python3.12"
#   role             = aws_iam_role.post_upload.arn
#   handler          = "lambda_function.lambda_handler"
#   filename         = data.archive_file.post_upload.output_path
#   source_code_hash = data.archive_file.post_upload.output_base64sha256

#   environment {
#     variables = {
#       QUEUE_URL = aws_sqs_queue.ascii_jobs.id
#     }
#   }
# }

# resource "aws_s3_bucket_notification" "upload_events" {
#   bucket = var.media_bucket_name

#   lambda_function {
#     lambda_function_arn = aws_lambda_function.post_upload.arn
#     events              = ["s3:ObjectCreated:Put"]
#     filter_prefix       = "uploads/"
#   }
# }

# resource "aws_sfn_state_machine_event_source_mapping" "sqs_to_sfn" {
#   event_source_arn  = aws_sqs_queue.ascii_jobs.arn
#   state_machine_arn = var.step_function_arn
#   enabled           = true
#   batch_size        = 1
# }
