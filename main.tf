terraform {
  backend "s3" {}
}

data "terraform_remote_state" "ecr" {
  backend = "s3"

  config = {
    bucket = "oidc-github-${data.aws_caller_identity.current.account_id}"
    key    = "${var.stage}/ecr/infra.tfstate"
    region = var.region
  }
}

data "local_file" "config" {
  filename = "${path.module}/config.json"
}

locals {
  config = jsondecode(data.local_file.config.content)
}

locals {
  function_name_downsize_media = local.config.lambda.function_name_downsize_media
  function_name_extract_audio  = local.config.lambda.function_name_extract_audio
  function_name_merge_frames   = local.config.lambda.function_name_merge_frames
  function_name_process_frames = local.config.lambda.function_name_process_frames
}

module "storage" {
  source     = "./modules/storage"
  stage      = var.stage
  region     = var.region
  account_id = data.aws_caller_identity.current.account_id
}

module "sfn" {
  source                              = "./modules/sfn"
  stage                               = var.stage
  media_bucket_arn                    = module.storage.media_bucket_arn
  audio_bucket_arn                    = module.storage.audio_bucket_arn
  ascii_art_bucket_arn                = module.storage.ascii_art_bucket_arn
  media_bucket_name                   = module.storage.media_bucket_name
  audio_bucket_name                   = module.storage.audio_bucket_name
  ascii_art_bucket_name               = module.storage.ascii_art_bucket_name
  lambda_function_name_downsize_media = "${local.function_name_downsize_media}-${var.stage}"
  lambda_function_name_extract_audio  = "${local.function_name_extract_audio}-${var.stage}"
  lambda_function_name_merge_frames   = "${local.function_name_merge_frames}-${var.stage}"
  lambda_function_name_process_frames = "${local.function_name_process_frames}-${var.stage}"
  lambda_image_downsize_media         = var.lambda_image_downsize_media
  lambda_image_extract_audio          = var.lambda_image_extract_audio
  lambda_image_merge_frames           = var.lambda_image_merge_frames
  lambda_image_process_frames         = var.lambda_image_process_frames
}
