variable "region" {
  type    = string
  default = "us-east-1"
}

variable "stage" {
  type    = string
  default = "dev"
}

variable "account_id" {
  type = string
}

variable "r2_access_key" {
  type      = string
  sensitive = true
}

variable "r2_secret_key" {
  type      = string
  sensitive = true
}

variable "cf_account_id" {
  type      = string
  sensitive = true
}
