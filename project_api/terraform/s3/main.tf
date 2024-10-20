## Will need to make a different tf file for each endpoint

variable "bucket_names" {
  type = list(string)
  description = "List of bucket names"
  default = []
}

# resource "aws_s3_bucket" "buckets" {
#   count  = length(var.bucket_names)
#   bucket = var.bucket_names[count.index]
#
#   tags = {
#     "Terraform" = "true"
#     "Name"      = var.bucket_names[count.index]
#   }
# }

# output "s3_bucket_arns" {
#   value = [for bucket in aws_s3_bucket.buckets : bucket.arn]
# }
resource "aws_s3_bucket" "bucket" {
  for_each = toset(var.bucket_names)

  bucket = each.value

  tags = {
    "terraform" = "true"
    "Name"      = each.value
  }
}
output "s3_bucket_info" {
  value = { for bucket in aws_s3_bucket.bucket : bucket.id => {
    arn   = bucket.arn
    tags  = bucket.tags
  }}
}



