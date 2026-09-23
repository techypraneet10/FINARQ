# ==============================================================================
# Compute Module - ECS Fargate API & Ingestion Worker Services
# ==============================================================================

# IAM Roles
data "aws_iam_policy_document" "ecs_assume_role" {
  statement {
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "task_execution" {
  name               = "${var.environment}-financial-rag-task-execution-role"
  assume_role_policy = data.aws_iam_policy_document.ecs_assume_role.json

  tags = merge(
    var.tags,
    {
      Environment = var.environment
    }
  )
}

resource "aws_iam_role_policy_attachment" "task_execution" {
  role       = aws_iam_role.task_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role" "app_task" {
  name               = "${var.environment}-financial-rag-app-task-role"
  assume_role_policy = data.aws_iam_policy_document.ecs_assume_role.json

  tags = merge(
    var.tags,
    {
      Environment = var.environment
    }
  )
}

# Grant S3 Bucket Access to App Task Role
resource "aws_iam_policy" "s3_access" {
  name        = "${var.environment}-financial-rag-s3-access"
  description = "Allows API and Worker tasks to read/write financial documents in S3"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          var.documents_bucket_arn,
          "${var.documents_bucket_arn}/*"
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "app_task_s3" {
  role       = aws_iam_role.app_task.name
  policy_arn = aws_iam_policy.s3_access.arn
}

# Security Groups
resource "aws_security_group" "api" {
  name        = "${var.environment}-financial-rag-api-sg"
  description = "Security group for Financial RAG FastAPI service"
  vpc_id      = var.vpc_id

  ingress {
    description     = "Allow HTTP traffic from Application Load Balancer only"
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [var.alb_security_group_id]
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
      Name        = "${var.environment}-api-sg"
      Environment = var.environment
    }
  )
}

resource "aws_security_group" "worker" {
  name        = "${var.environment}-financial-rag-worker-sg"
  description = "Security group for Financial RAG Ingestion Worker"
  vpc_id      = var.vpc_id

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(
    var.tags,
    {
      Name        = "${var.environment}-worker-sg"
      Environment = var.environment
    }
  )
}

# CloudWatch Log Groups
resource "aws_cloudwatch_log_group" "api" {
  name              = "/ecs/${var.environment}-financial-rag-api"
  retention_in_days = 30

  tags = merge(
    var.tags,
    {
      Environment = var.environment
    }
  )
}

resource "aws_cloudwatch_log_group" "worker" {
  name              = "/ecs/${var.environment}-financial-rag-worker"
  retention_in_days = 30

  tags = merge(
    var.tags,
    {
      Environment = var.environment
    }
  )
}

# API Task Definition & Service
resource "aws_ecs_task_definition" "api" {
  family                   = "${var.environment}-financial-rag-api"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.api_cpu
  memory                   = var.api_memory
  execution_role_arn       = aws_iam_role.task_execution.arn
  task_role_arn            = aws_iam_role.app_task.arn

  container_definitions = jsonencode([
    {
      name      = "api"
      image     = var.container_image
      essential = true
      command   = ["api"]
      portMappings = [
        {
          containerPort = 8000
          hostPort      = 8000
          protocol      = "tcp"
        }
      ]
      environment = var.common_environment_variables
      secrets     = var.common_secrets
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.api.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "api"
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

resource "aws_ecs_service" "api" {
  name            = "${var.environment}-financial-rag-api"
  cluster         = var.ecs_cluster_id
  task_definition = aws_ecs_task_definition.api.arn
  desired_count   = var.api_desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets         = var.subnet_ids
    security_groups = [aws_security_group.api.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = var.target_group_arn
    container_name   = "api"
    container_port   = 8000
  }

  tags = merge(
    var.tags,
    {
      Environment = var.environment
    }
  )
}

# Worker Task Definition & Service
resource "aws_ecs_task_definition" "worker" {
  family                   = "${var.environment}-financial-rag-worker"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = var.worker_cpu
  memory                   = var.worker_memory
  execution_role_arn       = aws_iam_role.task_execution.arn
  task_role_arn            = aws_iam_role.app_task.arn

  container_definitions = jsonencode([
    {
      name      = "worker"
      image     = var.container_image
      essential = true
      command   = ["worker"]
      environment = concat(
        var.common_environment_variables,
        [
          { name = "WORKER_CONCURRENCY", value = tostring(var.worker_concurrency) }
        ]
      )
      secrets = var.common_secrets
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.worker.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "worker"
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

resource "aws_ecs_service" "worker" {
  name            = "${var.environment}-financial-rag-worker"
  cluster         = var.ecs_cluster_id
  task_definition = aws_ecs_task_definition.worker.arn
  desired_count   = var.worker_desired_count
  launch_type     = "FARGATE"

  network_configuration {
    subnets         = var.subnet_ids
    security_groups = [aws_security_group.worker.id]
    assign_public_ip = false
  }

  tags = merge(
    var.tags,
    {
      Environment = var.environment
    }
  )
}
