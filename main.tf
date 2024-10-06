# data "terraform_remote_state" "ecr" {
#   backend = "s3"
#   config = {
#     bucket = "oidc-github-${data.aws_caller_identity.current.account_id}"
#     key    = "${var.stage}/infra.tfstate"
#     region = var.region
#   }
# }

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
  function_name_downsize_media  = local.config.lambda.function_name_downsize_media
  function_name_extract_audio   = local.config.lambda.function_name_extract_audio
  function_name_merge_frames    = local.config.lambda.function_name_merge_frames
  function_name_proccess_frames = local.config.lambda.function_name_proccess_frames
  function_name_split_frames    = local.config.lambda.function_name_split_frames
}

module "sfn" {
  source                               = "./modules/sfn"
  stage                                = var.stage
  lambda_function_name_downsize_media  = "${local.function_name_downsize_media}-${var.stage}"
  lambda_function_name_extract_audio   = "${local.function_name_extract_audio}-${var.stage}"
  lambda_function_name_merge_frames    = "${local.function_name_merge_frames}-${var.stage}"
  lambda_function_name_proccess_frames = "${local.function_name_proccess_frames}-${var.stage}"
  lambda_function_name_split_frames    = "${local.function_name_split_frames}-${var.stage}"
  lambda_image_downsize_media          = var.lambda_image_downsize_media
  lambda_image_extract_audio           = var.lambda_image_extract_audio
  lambda_image_merge_frames            = var.lambda_image_merge_frames
  lambda_image_proccess_frames         = var.lambda_image_proccess_frames
  lambda_image_split_frames            = var.lambda_image_split_frames
}
