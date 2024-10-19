## Will need to make a different tf file for each endpoint

variable "bucket_name" {}

resource "aws_s3_bucket" "bucket" {
  bucket = var.bucket_name

  tags = {
    "terraform" = "true"
    "Name"      = var.bucket_name
  }
}

output "s3_bucket_arn" {
  value = aws_s3_bucket.bucket.arn
}
