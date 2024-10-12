data "aws_caller_identity" "current" {}

terraform {
  backend "s3" {}
}

variable "ecr_lifecycle_policy" {
  type    = string
  default = <<EOF
{
    "rules": [
        {
            "rulePriority": 1,
            "description": "Keep last 3 images",
            "selection": {
                "tagStatus": "tagged",
                "tagPrefixList": ["v"],
                "countType": "imageCountMoreThan",
                "countNumber": 3
            },
            "action": {
                "type": "expire"
            }
        }
    ]
}
EOF
}

resource "aws_ecr_repository" "downsize_media" {
  name = var.lambda_function_name_downsize_media
}

resource "aws_ecr_lifecycle_policy" "downsize_media" {
  repository = aws_ecr_repository.downsize_media.name
  policy     = var.ecr_lifecycle_policy
}

resource "aws_ecr_repository" "downsize_video" {
  name = var.lambda_function_name_downsize_video
}

resource "aws_ecr_lifecycle_policy" "downsize_video" {
  repository = aws_ecr_repository.downsize_video.name
  policy     = var.ecr_lifecycle_policy
}

resource "aws_ecr_repository" "extract_audio" {
  name = var.lambda_function_name_extract_audio
}

resource "aws_ecr_lifecycle_policy" "extract_audio" {
  repository = aws_ecr_repository.extract_audio.name
  policy     = var.ecr_lifecycle_policy
}

resource "aws_ecr_repository" "merge_frames" {
  name = var.lambda_function_name_merge_frames
}

resource "aws_ecr_lifecycle_policy" "merge_frames" {
  repository = aws_ecr_repository.merge_frames.name
  policy     = var.ecr_lifecycle_policy
}

resource "aws_ecr_repository" "process_frames" {
  name = var.lambda_function_name_process_frames
}

resource "aws_ecr_lifecycle_policy" "process_frames" {
  repository = aws_ecr_repository.process_frames.name
  policy     = var.ecr_lifecycle_policy
}
