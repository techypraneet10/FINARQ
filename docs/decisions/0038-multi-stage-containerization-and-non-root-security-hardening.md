# ADR 0038: Multi-Stage Containerization and Non-Root Security Hardening

## Status
Accepted

## Context
Production containers must minimize attack surface area, avoid bundling unnecessary compilers/build tools in runtime images, and prevent running as root (`UID 0`) to enforce defense-in-depth against container breakout vulnerabilities.

## Decision
We implement a multi-stage Docker build workflow:
1. **Stage 1 (Builder)**: Base image `python:3.12-slim` installs `build-essential`, compiles Python dependencies into an isolated virtual environment `/opt/venv`, and discards all intermediate build tools.
2. **Stage 2 (Runtime)**: Clean `python:3.12-slim` base copies only the virtualenv `/opt/venv` and required runtime source files.
3. **Non-Root Execution**: Creates dedicated system user `appuser:appgroup` with explicit `UID 10001` and `GID 10001`. The container runs strictly as `USER 10001:10001`.
4. **Read-Only / Principle of Least Privilege**: Writable filesystem paths are strictly constrained to `/app/data/storage` and `/tmp`.
5. **Entrypoint Script**: Dispatches execution to `api`, `worker`, or `migrate` modes.

## Consequences
### Positive
- Small runtime image footprint (~250MB vs >1GB).
- Prevents privilege escalation and container escape risks.
- Enforces single container image artifact tested across staging and production.
