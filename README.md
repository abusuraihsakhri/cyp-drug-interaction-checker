# CYP Drug Interaction Checker

### [Open the Live Application →](https://abusuraihsakhri.github.io/cyp-drug-interaction-checker/)

A small, open-source **CYP450 drug-role reference lookup** with command-line, batch CSV, browser, and FastAPI interfaces. The built-in catalog contains 25 records across CYP3A4, CYP2D6, CYP2C19, CYP2C9, CYP1A2, and CYP2B6.

> **Clinical limitation:** This is an educational catalog, **not** a clinically validated drug–drug interaction rules engine. The labels `major`, `moderate`, and `minor` are inherited record tags, not evidence-based risk assessments for any drug pair. No interaction absence or medication safety can be inferred from a missing catalog match. Check current official labeling and clinical interaction resources before prescribing.

## Browser interface

Open `web/index.html` in a browser, or serve the project with FastAPI. The static interface supports text lookup, CSV upload, preview, and CSV export. Its JS dataset is verified against the Python catalog in CI.

**Browser privacy:** Lookup and uploaded CSV data are processed in local memory. No browser input is sent to the application server, and the page loads no external JS, fonts, or analytics. Do not upload identifiable patient data.

## Python quickstart

Requires Python 3.10–3.12.

```sh
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt

python cyp_checker.py single ketoconazole
python cyp_checker.py single --query "CYP2D6 inhibitor"
python cyp_checker.py batch --input sample.csv --output results.csv
python -m pytest -q
```

CSV input requires a header. Prefer `query` or `drug`; otherwise the first column is searched. The CLI adds `top_hit`, `lookup_score`, `interaction_type`, and `severity` columns. Search scores indicate **string relevance**, not interaction probability, pharmacokinetic effect or clinical severity.

## API and container

```sh
python cli.py serve --host 127.0.0.1 --port 8000
# Browser: http://127.0.0.1:8000/
# Interactive API docs: http://127.0.0.1:8000/docs
# GET /api/lookup?query=simvastatin
# GET /health and /metrics (JSON)
```

```sh
docker build -t cyp-drug-interaction-checker .
docker run --rm -p 8000:8000 -e AUDIT_SECRET_KEY="your-long-secret" cyp-drug-interaction-checker
```

The legacy experimental `cli.py audit`, `cli.py chat`, `cli.py batch`, `/api/audit`, and `/api/chat` workflows remain available. **They operate on synthetic generic thresholds; they do not perform pharmacological interaction prediction or clinical validation.** The mock chat adapter does not call an external model.

The audit trail uses an HMAC-SHA256 hash chain held **in process memory**, with verification of signatures and links. Set `AUDIT_SECRET_KEY` for a stable key. This is not persistent storage, a clinical audit system, or proof of HIPAA compliance. Identifier checks use heuristic patterns and may miss sensitive information; never input PHI.

## Development and testing

```sh
python -m pytest -q
python -m compileall -q agents cyp_checker.py enrichment.py cli.py simulator.py
node --check web/app.js
node --test tests/web.test.cjs
```

GitHub Actions runs Python tests for 3.10/3.11/3.12, browser JavaScript tests with Node 22, and Python/JS catalog parity checks. The static browser frontend does **not** require Python or Pyodide; the FastAPI backend and legacy supervisor require a Python server. Modern browsers supporting ES2021 APIs are expected to work; browser-device testing should be performed before clinical or institutional use.

## Technology and license

Python standard library, FastAPI, Pydantic, and vanilla HTML/CSS/JavaScript. Licensed under the [MIT License](LICENSE).
