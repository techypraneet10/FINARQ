# ADR 0041: Immutable Semantic Container Versioning and Zero-Downtime Deployment

## Status
Accepted

## Context
Deploying software using mutable tags (such as `latest`) leads to non-reproducible releases, untraceable bug regressions, and inability to safely rollback. Deployments must support seamless zero-downtime rolling updates.

## Decision
We enforce immutable semantic versioning and rolling zero-downtime deployment pipelines:
1. **Immutable ECR Tagging**: Every container image built in CI is tagged with the exact Git SHA and SemVer tag (`vX.Y.Z-<short-sha>`). The tag `latest` is strictly forbidden in production.
2. **Version Metadata Exposure**: Endpoints `GET /api/v1/version` and `GET /version` report the active Git SHA, build timestamp, environment, and application version.
3. **Rolling Zero-Downtime ECS Deployments**: ECS Fargate service updates use `minimum_healthy_percent = 100` and `maximum_percent = 200`. New tasks must pass healthchecks on `/health` before old tasks are drained and deregistered.
4. **Staging Gate & Smoke Testing**: Changes are automatically deployed to staging and validated via `tests/deployment/test_smoke.py` before requiring manual sign-off for production.

## Consequences
### Positive
- 100% reproducible deployments and deterministic rollback capability.
- Zero downtime during production releases.
