output "primary_endpoint_address" {
  value       = aws_elasticache_replication_group.main.primary_endpoint_address
  description = "Primary Redis write endpoint address"
}

output "reader_endpoint_address" {
  value       = aws_elasticache_replication_group.main.reader_endpoint_address
  description = "Read replica endpoint address"
}

output "port" {
  value       = aws_elasticache_replication_group.main.port
  description = "Port used by Redis (6379)"
}

output "security_group_id" {
  value       = aws_security_group.redis.id
  description = "Security Group ID of Redis cluster"
}
