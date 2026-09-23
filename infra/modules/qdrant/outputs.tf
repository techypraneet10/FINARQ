output "security_group_id" {
  value       = aws_security_group.qdrant.id
  description = "Security Group ID of Qdrant cluster"
}

output "service_name" {
  value       = aws_ecs_service.qdrant.name
  description = "ECS Service name for Qdrant"
}

output "dns_endpoint" {
  value       = "qdrant.financial-rag.local"
  description = "Internal service discovery DNS address for Qdrant"
}

output "port" {
  value       = 6333
  description = "Qdrant REST port"
}
