variable "stage" {
  type = string
}

variable "lambda_function_name_downsize_media" {
  type = string
}

variable "lambda_function_name_extract_audio" {
  type = string
}

variable "lambda_function_name_merge_frames" {
  type = string
}

variable "lambda_function_name_process_frames" {
  type = string
}

variable "lambda_image_downsize_media" {
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

variable "media_bucket_arn" {
  type = string
}

variable "audio_bucket_arn" {
  type = string
}

variable "ascii_art_bucket_arn" {
  type = string
}

variable "media_bucket_name" {
  type = string
}

variable "audio_bucket_name" {
  type = string
}

variable "ascii_art_bucket_name" {
  type = string
}
