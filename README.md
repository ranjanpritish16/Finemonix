# FinSentry

FinSentry is an ML-powered financial intelligence platform for Indian MSMEs that ingests multi-source financial data (Tally XML, GST JSON, bank CSVs) and delivers three core capabilities: a 90-day cash flow forecast powered by a Prophet/LSTM hybrid model, a loan eligibility engine using calibrated XGBoost classifiers with SHAP-based explainability for sub-100ms what-if analysis, and a regulatory risk monitor that scrapes BSE filings, extracts promoter pledge data and auditor opinions via NLP, detects anomalies using Isolation Forest, and maps entity relationships in a Neo4j knowledge graph.

---

## How to Run

### Prerequisites
- Docker & Docker Compose
- Python 3.11+

### Steps

```bash
# 1. Clone the repository
git clone <repo-url>
cd Neev_Finance

# 2. Set up environment variables
cp .env.example .env
# Open .env and fill in your passwords / secrets

# 3. Start all infrastructure services
docker-compose up -d postgres redis neo4j qdrant

# 4. Install backend dependencies
pip install -r backend/requirements.txt

# 5. Run DB startup checks (creates tables, constraints, Qdrant collection)
python backend/startup_checks.py

# 6. Start the FastAPI server
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

# 7. (Optional) Start Celery worker in a separate terminal
celery -A backend.tasks.celery_app worker --loglevel=info

# 8. API docs available at
#    http://localhost:8000/docs
```

### Run with Docker Compose (all services)

```bash
docker-compose up --build
```
