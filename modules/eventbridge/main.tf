locals {
  lambda_arns_to_warm = {
    downsize_media  = var.lambda_arn_downsize_media
    downsize_video  = var.lambda_arn_downsize_video
    extract_audio   = var.lambda_arn_extract_audio
    merge_frames    = var.lambda_arn_merge_frames
    process_frames  = var.lambda_arn_process_frames
    process_image   = var.lambda_arn_process_image
  }
  warmer_rule_name = "warm-lambda-rule-${var.stage}"
}

resource "aws_cloudwatch_event_rule" "lambda_warmer_rule" {
  name                = local.warmer_rule_name
  description         = "Triggers specified Lambdas periodically to keep them warm."
  schedule_expression = "rate(5 minutes)"
  is_enabled          = true
  tags = {
    Environment = var.stage
    Purpose     = "Lambda Warmer"
  }
}

resource "aws_lambda_permission" "allow_cloudwatch_to_invoke" {
  for_each = local.lambda_arns_to_warm
  statement_id  = "AllowExecutionFromCloudWatch_${each.key}_${var.stage}"
  action        = "lambda:InvokeFunction"
  function_name = each.value
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.lambda_warmer_rule.arn
}

resource "aws_cloudwatch_event_target" "warm_lambda_target" {
  for_each = local.lambda_arns_to_warm
  rule = aws_cloudwatch_event_rule.lambda_warmer_rule.name
  arn  = each.value
  target_id = "Warm_${each.key}_${var.stage}"
  input = jsonencode({
    "warm" : true
  })
  depends_on = [aws_lambda_permission.allow_cloudwatch_to_invoke]
}
