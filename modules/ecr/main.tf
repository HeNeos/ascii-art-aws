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
  repository = aws_ecr_repository.downsize_media
  policy     = var.ecr_lifecycle_policy
}

resource "aws_ecr_repository" "downsize_video" {
  name = var.lambda_function_name_downsize_video
}

resource "aws_ecr_lifecycle_policy" "downsize_media" {
  repository = aws_ecr_repository.downsize_video
  policy     = var.ecr_lifecycle_policy
}

resource "aws_ecr_repository" "extract_audio" {
  name = var.lambda_function_name_extract_audio
}

resource "aws_ecr_lifecycle_policy" "downsize_media" {
  repository = aws_ecr_repository.extract_audio
  policy     = var.ecr_lifecycle_policy
}

resource "aws_ecr_repository" "merge_frames" {
  name = var.lambda_function_name_merge_frames
}

resource "aws_ecr_lifecycle_policy" "downsize_media" {
  repository = aws_ecr_repository.merge_frames
  policy     = var.ecr_lifecycle_policy
}

resource "aws_ecr_repository" "process_frames" {
  name = var.lambda_function_name_process_frames
}

resource "aws_ecr_lifecycle_policy" "downsize_media" {
  repository = aws_ecr_repository.process_frames
  policy     = var.ecr_lifecycle_policy
}
