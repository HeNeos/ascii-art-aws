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

variable "region" {
  type    = string
  default = "us-east-1"
}

variable "stage" {
  type    = string
  default = "dev"
}
