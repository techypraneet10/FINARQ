# Developer Setup Guide

## Local Environment Prerequisites
- Python `>= 3.11` (Python 3.12 recommended)
- Git
- Docker and Docker Compose (optional for Phase 0, required for Phase 1+)

---

## Step-by-Step Setup

### 1. Clone the Repository
```bash
git clone <repository_url>
cd financial-rag-platform
```

### 2. Create and Activate Virtual Environment
```bash
# On Linux / macOS
python3 -m venv .venv
source .venv/bin/activate

# On Windows (PowerShell)
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Install Dependencies
```bash
pip install --upgrade pip
pip install -e ".[dev]"
```

### 4. Configure Environment Variables
```bash
cp .env.example .env
```
*(In Phase 0, default values in `.env.example` are sufficient to run all services and tests locally without any cloud credentials).*

---

## Running the Application

### Option A: Direct Uvicorn Execution
```bash
uvicorn financial_rag.main:app --reload --port 8000
```

### Option B: Cross-Platform Python Helper Script
```bash
python scripts/run_dev.py
```

### Option C: Docker Container
```bash
docker compose build
docker compose up -d
```

Verify service is running:
```bash
curl http://localhost:8000/health
```

---

## Running Tests & Code Quality Checks

### Run Test Suite
```bash
# Run pytest with test coverage report
pytest --cov=src/financial_rag tests/

# Or via script
python scripts/test.py
```

### Linting & Formatting
```bash
# Check linting
ruff check .

# Check formatting
ruff format --check .

# Auto-format files
ruff format .
```

### Static Type Checking
```bash
mypy src tests
```

### All-in-One Quality Check
```bash
python scripts/lint.py
```
