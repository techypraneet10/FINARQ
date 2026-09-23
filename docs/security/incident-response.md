# Financial RAG Platform — Security Incident Response Runbook

## 1. Incident Response Lifecycle
This runbook provides actionable procedures for engineering teams detecting, triaging, containing, investigating, and recovering from security incidents.

```
[ 1. Detection & Alerting ]
            │ (Prometheus Alert, Audit Log Anomaly, Telemetry Spike)
            ▼
[ 2. Triage & Severity Classification ]
            │ (P1 Critical: Data Breach / Cross-Tenant Leak; P2 High: Auth/Token Compromise)
            ▼
[ 3. Containment & Isolation ]
            │ (Revoke Tokens, Suspend Tenant/User, Block IP, Trip Circuit Breaker)
            ▼
[ 4. Eradication & Remediation ]
            │ (Rotate JWT Signing Keys, Rotate DB/Storage Secrets, Deploy Patch)
            ▼
[ 5. Recovery & Verification ]
            │ (Verify Health/Ready Probes, Run Security Regression Tests)
            ▼
[ 6. Post-Incident Review & RCA ]
```

---

## 2. Emergency Operational Playbooks

### Playbook A: Compromised User Credentials / Leaked Token
1. **Revoke All Active Refresh Tokens**:
   Execute database revocation for target user ID:
   ```sql
   UPDATE refresh_tokens SET revoked = TRUE WHERE user_id = :compromised_user_id;
   ```
2. **Suspend User Account**:
   ```sql
   UPDATE users SET status = 'suspended' WHERE id = :compromised_user_id;
   ```
3. **Audit Log Inspection**:
   Query all actions performed by user within incident window:
   ```sql
   SELECT * FROM audit_events WHERE actor_user_id = :compromised_user_id ORDER BY timestamp DESC;
   ```

---

### Playbook B: Suspected JWT Signing Secret Compromise
1. **Rotate Secret Key in Secrets Manager**:
   Update `SECURITY_JWT_SECRET_KEY` with a new cryptographically random 64-character secret.
2. **Restart API Instances**:
   Rolling restart forces immediate invalidation of all previously signed access tokens.
3. **Revoke All Stored Refresh Tokens**:
   ```sql
   UPDATE refresh_tokens SET revoked = TRUE;
   ```
4. **Notify Users**:
   All active sessions are terminated; users must re-authenticate with credentials.

---

### Playbook C: Cross-Tenant Data Access Investigation
1. **Identify Anomalous Audit Events**:
   ```sql
   SELECT * FROM audit_events 
   WHERE event_type IN ('UNAUTHORIZED_ACCESS_ATTEMPT', 'CROSS_TENANT_ACCESS_ATTEMPT') 
   ORDER BY timestamp DESC;
   ```
2. **Review Storage Access Logs**:
   Confirm whether raw binary files were requested or accessed.
3. **Assess Blast Radius**:
   Determine exact tenant organizations, documents, and timestamp ranges involved.
4. **Preserve Forensic Evidence**:
   Snapshot PostgreSQL audit tables and object storage access logs before any remediation.
