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
  function_name_downsize_video = local.config.lambda.function_name_downsize_video
  function_name_extract_audio  = local.config.lambda.function_name_extract_audio
  function_name_merge_frames   = local.config.lambda.function_name_merge_frames
  function_name_process_frames = local.config.lambda.function_name_process_frames
  function_name_process_image  = local.config.lambda.function_name_process_image
}

module "storage" {
  source        = "./modules/storage"
  stage         = var.stage
  region        = var.region
  account_id    = data.aws_caller_identity.current.account_id
  cf_account_id = var.cf_account_id
  r2_access_key = var.r2_access_key
  r2_secret_key = var.r2_secret_key
}

module "api" {
  source            = "./modules/api"
  stage             = var.stage
  region            = var.region
  account_id        = data.aws_caller_identity.current.account_id
  media_bucket_arn  = module.storage.media_bucket_arn
  media_bucket_name = module.storage.media_bucket_name
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
  r2_secrets_bucket_name              = module.storage.r2_secrets_bucket_name
  r2_secrets_bucket_arn               = module.storage.r2_secrets_bucket_arn
  status_table_name                   = module.api.status_table_name
  status_table_arn                    = module.api.status_table_arn
  lambda_function_name_downsize_media = "${local.function_name_downsize_media}-${var.stage}"
  lambda_function_name_downsize_video = "${local.function_name_downsize_video}-${var.stage}"
  lambda_function_name_extract_audio  = "${local.function_name_extract_audio}-${var.stage}"
  lambda_function_name_merge_frames   = "${local.function_name_merge_frames}-${var.stage}"
  lambda_function_name_process_frames = "${local.function_name_process_frames}-${var.stage}"
  lambda_function_name_process_image  = "${local.function_name_process_image}-${var.stage}"
  lambda_image_downsize_media         = var.lambda_image_downsize_media
  lambda_image_downsize_video         = var.lambda_image_downsize_video
  lambda_image_extract_audio          = var.lambda_image_extract_audio
  lambda_image_merge_frames           = var.lambda_image_merge_frames
  lambda_image_process_frames         = var.lambda_image_process_frames
  lambda_image_process_image          = var.lambda_image_process_image
}

module "eventbridge" {
  source = "./modules/eventbridge"
  stage = var.stage
  lambda_arn_downsize_media = module.sfn.lambda_arn_downsize_media
  lambda_arn_downsize_video = module.sfn.lambda_arn_downsize_video
  lambda_arn_extract_audio = module.sfn.lambda_arn_extract_audio
  lambda_arn_merge_frames = module.sfn.lambda_arn_merge_frames
  lambda_arn_process_frames = module.sfn.lambda_arn_process_frames
  lambda_arn_process_image = module.sfn.lambda_arn_process_image
}

# module "sqs" {
#   source            = "./modules/sqs"
#   stage             = var.stage
#   region            = var.region
#   account_id        = data.aws_caller_identity.current.account_id
#   media_bucket_arn  = module.storage.media_bucket_arn
#   media_bucket_name = module.storage.media_bucket_name
#   step_function_arn = module.sfn.step_function_arn
# }
