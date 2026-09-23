# ==============================================================================
# Qdrant Vector Store Module - Private Subnet Deployment
# ==============================================================================

resource "aws_security_group" "qdrant" {
  name        = "${var.environment}-financial-rag-qdrant-sg"
  description = "Controls access to Qdrant vector database from API and Worker tasks"
  vpc_id      = var.vpc_id

  ingress {
    description     = "Inbound HTTP access to Qdrant REST API (port 6333)"
    from_port       = 6333
    to_port         = 6333
    protocol        = "tcp"
    security_groups = var.allowed_security_group_ids
  }

  ingress {
    description     = "Inbound gRPC access to Qdrant (port 6334)"
    from_port       = 6334
    to_port         = 6334
    protocol        = "tcp"
    security_groups = var.allowed_security_group_ids
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(
    var.tags,
    {
      Name        = "${var.environment}-qdrant-sg"
      Environment = var.environment
    }
  )
}

# CloudWatch Log Group for Qdrant
resource "aws_cloudwatch_log_group" "qdrant" {
  name              = "/ecs/${var.environment}-financial-rag-qdrant"
  retention_in_days = 30

  tags = merge(
    var.tags,
    {
      Environment = var.environment
    }
  )
}

# ECS Task Definition for Qdrant
resource "aws_ecs_task_definition" "qdrant" {
  family                   = "${var.environment}-financial-rag-qdrant"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.cpu
  memory                   = var.memory
  execution_role_arn       = var.execution_role_arn
  task_role_arn            = var.task_role_arn

  container_definitions = jsonencode([
    {
      name      = "qdrant"
      image     = var.qdrant_image
      essential = true
      portMappings = [
        {
          containerPort = 6333
          hostPort      = 6333
          protocol      = "tcp"
        },
        {
          containerPort = 6334
          hostPort      = 6334
          protocol      = "tcp"
        }
      ]
      environment = [
        { name = "QDRANT__STORAGE__STORAGE_PATH", value = "/qdrant/storage" },
        { name = "QDRANT__SERVICE__ENABLE_TLS", value = "false" }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.qdrant.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "qdrant"
        }
      }
    }
  ])

  tags = merge(
    var.tags,
    {
      Environment = var.environment
    }
  )
}

# Service Discovery Namespace Registration
resource "aws_service_discovery_service" "qdrant" {
  name = "qdrant"

  dns_config {
    namespace_id = var.service_discovery_namespace_id

    dns_records {
      ttl  = 10
      type = "A"
    }

    routing_policy = "MULTIVALUE"
  }

  health_check_custom_config {
    failure_threshold = 2
  }
}

# ECS Service for Qdrant
resource "aws_ecs_service" "qdrant" {
  name            = "${var.environment}-financial-rag-qdrant"
  cluster         = var.ecs_cluster_id
  task_definition = aws_ecs_task_definition.qdrant.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets         = var.subnet_ids
    security_groups = [aws_security_group.qdrant.id]
    assign_public_ip = false
  }

  service_registries {
    registry_arn = aws_service_discovery_service.qdrant.arn
  }

  tags = merge(
    var.tags,
    {
      Environment = var.environment
    }
  )
}
