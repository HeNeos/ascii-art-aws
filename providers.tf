data "aws_caller_identity" "current" {}

# terraform {
#   backend "s3" {
#     bucket = "oidc-github-${data.aws_caller_identity.current.account_id}"
#     key    = "${var.stage}/infra.tfstate"
#   }
# }

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
  }
}

provider "aws" {
  region = var.region
}
