variable "db_name" {
  description = "The name of the database"
}

variable "db_instance_class" {
  description = "The instance type for the RDS instance"
}

variable "engine" {
  description = "The database engine to use"
}

variable "username" {
  description = "The username for the database"
}

variable "password" {
  description = "The password for the database"
}

resource "aws_db_instance" "default" {
  identifier          = var.db_name
  engine             = var.engine
  instance_class     = var.db_instance_class
  username           = var.username
  password           = var.password
  db_name            = var.db_name
  allocated_storage   = 20
  skip_final_snapshot = true # Set to false if you want to take a snapshot before deletion

  tags = {
    "terraform" = "true"
    "Name"      = var.db_name
  }
}

output "db_instance_arn" {
  value = aws_db_instance.default.arn
}
