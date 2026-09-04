# CYP Drug Interaction Checker

> **Domain:** Computational Biology & AI Drug Discovery  
> **Reference Guidelines & Standards:** `wwPDB, IUPAC & CLSI Computational Guidelines`

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## 📖 What It Does

CYP Drug Interaction Checker is a tool for identifying and classifying CYP450 drug-drug interactions. It supports:

- **Single drug lookup** with token overlap and substring scoring
- **Batch CSV processing** for high-throughput screening
- **Severity tier classification** (major, moderate, minor)
- **Interaction type identification** (substrate, inhibitor, inducer)

---

## ⚙️ Key Capabilities & Algorithmic Modules

### 🔬 Analytical Functions

- **`lookup()`**: Single drug lookup using token overlap + substring scoring. Returns top hits with interaction type and severity.
- **`process_csv()`**: Batch processing of CSV files with drug interaction lookups.
- **`build_parser()`**: CLI argument parser construction.
- **`main()`**: CLI entry point.

---

## 📐 Scoring Algorithm

```text
score = 0
if key in query: score += 10          # Substring match bonus
score += token_overlap * 2             # Token overlap scoring
score += severity_weight               # Major=3, Moderate=2, Minor=1
```

---

## 💻 Installation

```bash
# Clone the repository
git clone https://github.com/abusuraihsakhri/cyp-drug-interaction-checker.git
cd cyp-drug-interaction-checker

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

---

## 💻 CLI Quickstart & Usage

### 1. Single Drug Lookup
```bash
python cyp_checker.py single ketoconazole
python cyp_checker.py single --query "simvastatin"
```

### 2. Batch CSV Processing
```bash
python cyp_checker.py batch --input sample.csv --output results.csv
```

### 3. Enterprise Supervisor Mode
```bash
# Run single audit task
python cli.py audit --task-id TASK-001 --primary 28.5 --secondary 14.2

# Batch process records
python cli.py batch -i sample.csv -o results.csv

# Verify audit trail integrity
python cli.py verify-audit

# Launch FastAPI REST server
python cli.py serve --host 127.0.0.1 --port 8000
```

### Input Data Schema

| Field | Description | Requirement |
|:------|:------------|:------------|
| `query` | Drug name or CYP interaction term | Required |
| `drug` | Alternative drug name column | Optional |

---

## 🛡️ Security & Enterprise Architecture

* **Zero-PHI Outbound Interceptor:** Active regex inspection blocking SSNs, MRNs, phone numbers, and patient identifiers.
* **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation.
* **FastAPI & Prometheus Telemetry:** Exposes OpenAPI 3.1 REST endpoints and operational Prometheus metrics (`/metrics`).

### Security Configuration

Set the `AUDIT_SECRET_KEY` environment variable for production use:

```bash
export AUDIT_SECRET_KEY="your-secure-random-key"
```

---

## 🧪 Testing & Verification

Run the automated test suite:

```bash
pytest -v
```

Execute high-throughput batch simulation benchmarks:

```bash
python simulator.py 1000
```

---

## 🐳 Container Deployment

```bash
# Build and run with Docker
docker build -t cyp-drug-interaction-checker .
docker run -p 8000:8000 -e AUDIT_SECRET_KEY=your-secret cyp-drug-interaction-checker

# Or use Docker Compose
AUDIT_SECRET_KEY=your-secret docker-compose up
```

---

## 📊 CYP450 Drug Database

The built-in database includes common CYP450 interactions:

| Enzyme | Interaction Type | Examples |
|:-------|:-----------------|:---------|
| CYP3A4 | Inhibitor | Ketoconazole, Itraconazole, Clarithromycin, Ritonavir |
| CYP3A4 | Substrate | Simvastatin, Midazolam, Cyclosporine |
| CYP3A4 | Inducer | Carbamazepine, Phenytoin, Rifampin |
| CYP2D6 | Inhibitor | Fluoxetine, Paroxetine, Quinidine |
| CYP2D6 | Substrate | Codeine, Tamoxifen, Metoprolol |
| CYP2C19 | Inhibitor | Omeprazole |
| CYP2C19 | Substrate | Clopidogrel |
| CYP2C9 | Inhibitor | Fluconazole |
| CYP2C9 | Substrate | Warfarin |
| CYP1A2 | Inhibitor | Fluvoxamine |
| CYP2B6 | Substrate | Efavirenz, Bupropion |
