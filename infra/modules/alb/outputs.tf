output "alb_arn" {
  value       = aws_lb.main.arn
  description = "ARN of the Application Load Balancer"
}

output "alb_dns_name" {
  value       = aws_lb.main.dns_name
  description = "Public DNS name of the ALB"
}

output "alb_zone_id" {
  value       = aws_lb.main.zone_id
  description = "Canonical Route53 Zone ID of the ALB"
}

output "security_group_id" {
  value       = aws_security_group.alb.id
  description = "Security Group ID of the ALB"
}

output "target_group_arn" {
  value       = aws_lb_target_group.api.arn
  description = "ARN of the API Target Group"
}
