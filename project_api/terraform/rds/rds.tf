variable "db_name" {
  description = "The name of the database"
}

variable "db_instance_class" {
  description = "The instance type for the RDS instance"
  default = "db.t3.micro"
}

variable "engine" {
  description = "The database engine to use"
  default = "mysql"
}

variable "username" {
  description = "The username for the database"
}

variable "password" {
  description = "The password for the database"
}

variable "allocated_storage" {
  description = "storage allocated for RDS"
  default = 20
}

resource "aws_db_instance" "default" {
  identifier          = var.db_name
  engine             = var.engine
  instance_class     = var.db_instance_class
  username           = var.username
  password           = var.password
  db_name            = var.db_name
  allocated_storage   = var.allocated_storage
  skip_final_snapshot = true

  tags = {
    "terraform" = "true"
    "Name"      = var.db_name
  }
}

output "db_instance_arn" {
  value = aws_db_instance.default.arn
}
