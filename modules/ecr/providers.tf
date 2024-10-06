data "aws_caller_identity" "current" {}

terraform {
  backend "s3" {
    bucket = "terraform-state-bucket-${data.aws_caller_identity.current.account_id}"
    key    = "${var.stage}/infra.tfstate"
  }
}
