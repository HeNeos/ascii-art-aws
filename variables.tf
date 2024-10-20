variable "region" {
  type    = string
  default = "us-east-1"
}

variable "stage" {
  type        = string
  description = "The deployment stage (dev, prod)"
  default     = "dev"
}

variable "lambda_image_downsize_media" {
  type = string
}

variable "lambda_image_downsize_video" {
  type = string
}

variable "lambda_image_extract_audio" {
  type = string
}

variable "lambda_image_merge_frames" {
  type = string
}

variable "lambda_image_process_frames" {
  type = string
}
