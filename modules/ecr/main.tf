resource "aws_ecr_repository" "downsize_media" {
  name = var.lambda_function_name_downsize_media
}

resource "aws_ecr_repository" "extract_audio" {
  name = var.lambda_function_name_extract_audio
}

resource "aws_ecr_repository" "merge_frames" {
  name = var.lambda_function_name_merge_frames
}

resource "aws_ecr_repository" "proccess_frames" {
  name = var.lambda_function_name_proccess_frames
}

resource "aws_ecr_repository" "split_frames" {
  name = var.lambda_function_name_split_frames
}
