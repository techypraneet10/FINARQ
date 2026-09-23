output "api_security_group_id" {
  value       = aws_security_group.api.id
  description = "Security Group ID of API tasks"
}

output "worker_security_group_id" {
  value       = aws_security_group.worker.id
  description = "Security Group ID of Worker tasks"
}

output "task_execution_role_arn" {
  value       = aws_iam_role.task_execution.arn
  description = "ARN of ECS task execution IAM role"
}

output "app_task_role_arn" {
  value       = aws_iam_role.app_task.arn
  description = "ARN of application task IAM role"
}

output "api_service_name" {
  value       = aws_ecs_service.api.name
  description = "Name of the API ECS service"
}

output "worker_service_name" {
  value       = aws_ecs_service.worker.name
  description = "Name of the Worker ECS service"
}
