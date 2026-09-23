# Prometheus & CloudWatch Production Alert Definitions

## 1. Alerting Philosophy

- **Actionable**: Every fired alert links directly to an approved runbook with clear resolution steps.
- **Tiered by Urgency**: Alerts are categorized into Severity 1 (Critical Pager), Severity 2 (High Ticket), and Severity 3 (Warning Digest).
- **Anti-Fatigue**: Dynamic hysteresis windows and sustained condition checks prevent alert storms on momentary spikes.

---

## 2. Alert Matrix & Severity Classification

### Severity 1: Critical (Immediate PagerDuty / On-Call Wake-Up)

| Alert Name | Condition | Evaluation Window | Runbook |
| :--- | :--- | :--- | :--- |
| `APIHighErrorRate5xx` | `sum(rate(http_requests_total{status=~"5.."}[5m])) / sum(rate(http_requests_total[5m])) > 0.05` | 2 minutes | [API Outage Runbook](file:///docs/operations/runbooks/api_outage.md) |
| `PostgresDown` | `pg_up == 0` or database connection pool failure | 1 minute | [Database Failover Runbook](file:///docs/operations/runbooks/database_failover.md) |
| `QdrantUnreachable` | `probe_success{target="qdrant"} == 0` for all nodes | 2 minutes | [Vector Rebuild Runbook](file:///docs/operations/runbooks/vector_rebuild.md) |
| `CircuitBreakerTrippedSustained` | `circuit_breaker_state{state="OPEN"} == 1` for > 5 min | 5 minutes | [API Outage Runbook](file:///docs/operations/runbooks/api_outage.md) |
| `CrossTenantIsolationViolation` | `security_tenant_isolation_violations_total > 0` | Immediate | [Security Incident Response](file:///docs/security/hardening_guide.md) |

### Severity 2: High (Slack #alerts-prod & JIRA Ticket)

| Alert Name | Condition | Evaluation Window | Runbook |
| :--- | :--- | :--- | :--- |
| `WorkerQueueBacklog` | `count(ingestion_jobs{status="pending"}) > 50` | 15 minutes | [Worker Backlog Runbook](file:///docs/operations/runbooks/worker_backlog.md) |
| `HighQueryLatencyP95` | `histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le)) > 5.0` | 10 minutes | [API Outage Runbook](file:///docs/operations/runbooks/api_outage.md) |
| `RedisMemoryHigh` | `redis_memory_used_bytes / redis_memory_max_bytes > 0.85` | 10 minutes | [Database Failover Runbook](file:///docs/operations/runbooks/database_failover.md) |
| `LLMHighErrorRate` | `sum(rate(llm_requests_total{status="error"}[10m])) / sum(rate(llm_requests_total[10m])) > 0.10` | 10 minutes | [API Outage Runbook](file:///docs/operations/runbooks/api_outage.md) |

### Severity 3: Warning (Daily Slack Digest & Grafana Notice)

| Alert Name | Condition | Evaluation Window | Runbook |
| :--- | :--- | :--- | :--- |
| `StorageTieringAnomaly` | S3 standard storage growth > 20% week-over-week | 24 hours | [Cost Model](file:///docs/architecture/cost_model.md) |
| `LowConfidenceClaimRate` | `grounding_fallback_rate > 0.05` | 1 hour | [SLO Framework](file:///docs/operations/slo_framework.md) |

---

## 3. Escalation & On-Call Policy

1. **Ack Window**: Severity 1 alerts must be acknowledged within **15 minutes**.
2. **Escalation**: Unacknowledged Sev-1 alerts escalate to the Secondary On-Call Engineer, then to the Platform Lead after 30 minutes.
3. **Post-Mortem**: Every Sev-1 incident requires a formal blameless post-mortem published within 48 business hours.
