variable "lambda_arn_downsize_media" {
  type = string
}

variable "lambda_arn_downsize_video" {
  type = string
}

variable "lambda_arn_extract_audio" {
  type = string
}

variable "lambda_arn_merge_frames" {
  type = string
}

variable "lambda_arn_process_frames" {
  type = string
}

variable "lambda_arn_process_image" {
  type = string
}

variable "region" {
  type    = string
  default = "us-east-1"
}

variable "stage" {
  type    = string
  default = "dev"
}
