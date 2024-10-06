variable "repository_name" {
  description = "The name of the ECR repository"
  type        = string
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

variable "lambda_function_name_proccess_frames" {
  type = string
}

variable "lambda_function_name_split_frames" {
  type = string
}
