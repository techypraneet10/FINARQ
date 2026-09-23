output "endpoint" {
  value       = aws_db_instance.main.endpoint
  description = "Connection endpoint for PostgreSQL RDS instance"
}

output "address" {
  value       = aws_db_instance.main.address
  description = "Hostname of PostgreSQL RDS instance"
}

output "port" {
  value       = aws_db_instance.main.port
  description = "Port for PostgreSQL database"
}

output "database_name" {
  value       = aws_db_instance.main.db_name
  description = "Database name"
}

output "security_group_id" {
  value       = aws_security_group.rds.id
  description = "Security Group ID of the RDS instance"
}

output "arn" {
  value       = aws_db_instance.main.arn
  description = "ARN of PostgreSQL RDS instance"
}
