# Finemonix - Financial Intelligence Platform

Finemonix is an ML-powered financial intelligence platform for Indian MSMEs that ingests multi-source financial data (Tally XML, GST JSON, bank CSVs) and delivers three core capabilities:

1. **90-Day Cash Flow Forecast** — Powered by a Prophet/LSTM hybrid model for accurate financial projections
2. **Loan Eligibility Engine** — Uses calibrated XGBoost classifiers with SHAP-based explainability for sub-100ms what-if analysis
3. **Regulatory Risk Monitor** — Scrapes BSE filings, extracts promoter pledge data and auditor opinions via NLP, detects anomalies using Isolation Forest, and maps entity relationships in a Neo4j knowledge graph

---

## Table of Contents
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [Environment Setup](#environment-setup)
- [Quick Start (Recommended)](#quick-start-recommended)
- [Manual Setup](#manual-setup)
- [Running the System](#running-the-system)
- [API Documentation](#api-documentation)
- [Development Workflow](#development-workflow)
- [Troubleshooting](#troubleshooting)

---

## Features

Finemonix comes equipped with powerful, production-ready features designed specifically for Indian MSMEs:

### 1. **Multi-Source Financial Data Integration**

Upload and process financial data from multiple sources seamlessly:

#### Tally ERP 9 / TallyPrime XML
- **What it extracts**: Transactions, invoices, ledger entries, and client information
- **How it works**: Parses Tally XML exports to extract detailed financial records
- **Special handling**: 
  - Multi-currency support with automatic INR conversion (USD, EUR, GBP rates)
  - Handles encoding issues common in Tally XML exports
  - Extracts both debit and credit transactions
  - Categorizes transactions by voucher type (Sales, Purchase, Payment, Contra)

**Example Usage**:
```bash
POST /api/data/upload
Content-Type: multipart/form-data

business_id=1&file_type=tally&file=accountsexport.xml
```

#### GST (Goods and Services Tax) JSON
- **What it extracts**: GST invoices, tax compliance data, GST filing information
- **How it works**: Parses GST JSON files containing invoice details and tax calculations
- **Key data**: GST registration numbers, invoice amounts, tax rates, invoice status

**Example Usage**:
```bash
POST /api/data/upload
Content-Type: multipart/form-data

business_id=1&file_type=gst&file=gst_invoices.json
```

#### Bank Statement CSV
- **What it extracts**: Bank transactions, account balance history, wire transfers
- **How it works**: Parses standard bank CSV exports with transaction details
- **Supports**: Multiple CSV formats common to Indian banks
- **Key fields**: Transaction date, amount, balance, narration/description

**Example Usage**:
```bash
POST /api/data/upload
Content-Type: multipart/form-data

business_id=1&file_type=bank&file=bank_statement.csv
```

### 2. **Intelligent Data Processing Pipeline**

Once data is uploaded, Finemonix automatically processes it through multiple stages:

#### Entity Resolution & Deduplication
- **Fuzzy String Matching**: Uses RapidFuzz to identify the same client/vendor across different data sources (e.g., "ABC Enterprises" vs "ABC Enterprises Pvt Ltd")
- **GSTIN Matching**: Authoritative matching using GST registration numbers (most reliable)
- **Semantic Similarity**: Uses sentence-transformers embeddings (all-MiniLM-L6-v2 model) for contextual name matching
- **Threshold**: 85% similarity score required for entity matching
- **Output**: Canonical entity records with aliases and relationship tracking

#### Transaction Aggregation
- Combines transactions from Tally, GST, and bank sources
- Deduplicates identical transactions (same date, amount, counterparty)
- Marks transaction source for audit trail (tally, gst, or bank)
- Creates unified transaction ledger

#### Invoice Tracking
- Extracts and tracks all invoices (sales and purchase)
- Tracks invoice status: `pending`, `paid`, `overdue`, `partial`
- Calculates days overdue automatically
- Identifies payment patterns and average payment delays by client

### 3. **Advanced Cash Flow Forecasting** ⭐

Finemonix uses a hybrid ML approach with two sophisticated models:

#### LSTM (Long Short-Term Memory) Neural Network
**Architecture**:
- Input: 60-day historical window of financial features
- 2 layers of LSTM with hidden size of 128
- MC Dropout (Bayesian uncertainty estimation) for confidence intervals
- Output: 90-day daily balance predictions with p10 (pessimistic) and p90 (optimistic) estimates

**Key Features**:
- **Deep Learning**: Learns complex temporal patterns in cash flow
- **Uncertainty Quantification**: MC Dropout provides probabilistic forecasts (10th and 90th percentiles)
- **Flexible Architecture**: Configurable hidden size, layers, and dropout rate

**Input Features**:
- Running balance (cash balance)
- Daily net cash flow
- Transaction count
- GST filing day indicators (helps predict seasonal patterns)
- Future invoice expectations

**Output**:
```json
{
  "forecast_date": "2026-06-15",
  "predicted_balance": 250000.50,
  "p10_balance": 180000.00,  # 10th percentile (pessimistic)
  "p90_balance": 320000.00,  # 90th percentile (optimistic)
  "model_used": "lstm",
  "model_version": "1.0"
}
```

#### Prophet Time Series Model
**Approach**: Facebook's Prophet for time-series decomposition and seasonal forecasting

**Key Features**:
- **Seasonality Detection**: Identifies weekly and monthly seasonal patterns
  - Weekly: 7-day periodicity with Fourier order 3
  - Monthly: 30.5-day periodicity with Fourier order 5
- **Regressors**: Uses external variables to improve accuracy
  - `is_gst_filing_day`: Binary indicator for GST compliance dates
  - `future_invoices`: Expected revenue from upcoming invoices
- **Interval Width**: 80% confidence intervals (16.67% on each tail)
- **Robust Forecasting**: Handles missing data and outliers automatically

**Output**:
```json
{
  "forecast_date": "2026-06-15",
  "yhat": 245000.00,        # Point forecast
  "yhat_lower": 200000.00,  # Lower bound
  "yhat_upper": 290000.00,  # Upper bound
  "model_used": "prophet"
}
```

#### Danger Zone Detection
Automatically identifies periods where cash flow falls below safety threshold:

```json
{
  "danger_zones": [
    {
      "start_date": "2026-06-20",
      "end_date": "2026-06-25",
      "min_balance": 25000.00,
      "shortfall": 25000.00,
      "severity": "critical"
    }
  ]
}
```

### 4. **Loan Eligibility & Risk Assessment** ⭐

Finemonix provides intelligent, multi-lender loan eligibility analysis with sub-25ms what-if inference:

**Architecture**:
- Calibrated XGBoost classifiers — one per lender type (PSU banks, NBFC, Private banks, MFIs)
- SHAP (SHapley Additive exPlanations) for explainable AI — waterfall chart on frontend
- O(1) what-if delta engine: pre-computed SHAP decompositions cached in Redis, delta approximated in a single fast pass (~5ms), full response under 25ms
- Loan CTA wired directly into cash flow forecast — contextual nudge when danger zone detected

**Lender Types Supported**:
| Lender | Model File | Typical Approval Range |
|--------|-----------|------------------------|
| PSU Banks | `psu_shap_values.npy` | Conservative, collateral-heavy |
| NBFC | `nbfc_shap_values.npy` | Higher approval, higher rate |
| Private Banks | `private_shap_values.npy` | Balanced risk/return |
| MFI | `mfi_shap_values.npy` | Micro-loan, low ticket size |

**Example What-If Request**:
```bash
POST /api/loan/eligibility
{
  "business_id": 1,
  "delay_days": 30,
  "amount_override": 500000
}
```

**Example What-If Response**:
```json
{
  "lenders": {
    "psu": { "probability": 0.28, "eligible": false },
    "nbfc": { "probability": 0.71, "eligible": true },
    "private": { "probability": 0.54, "eligible": true },
    "mfi": { "probability": 0.88, "eligible": true }
  },
  "shap_explanation": {
    "base_value": 0.45,
    "features": [
      { "name": "client_concentration", "shap_value": -0.18, "feature_value": 0.72 },
      { "name": "avg_payment_delay_days", "shap_value": -0.12, "feature_value": 30 },
      { "name": "revenue_stability", "shap_value": 0.21, "feature_value": 0.84 }
    ]
  },
  "response_ms": 22
}
```

### 5. **Real-time Dashboard & Analytics**

Comprehensive business health dashboard with real-time metrics:

**Available Metrics**:
- **Current Cash Balance**: Real-time balance from all transactions
- **Monthly Revenue**: Sum of all inbound transactions in current month
- **Monthly Expenses**: Sum of all outbound transactions in current month
- **Recent Transactions**: Last 5 transactions with details
- **Outstanding Invoices**: Pending and overdue invoices
- **Forecast Status**: Latest 90-day forecast with confidence intervals
- **Anomaly Alerts**: Real-time anomaly detection scores

**Example Dashboard Response**:
```json
{
  "business": {
    "id": 1,
    "name": "ABC Enterprises",
    "quality_score": 85
  },
  "current_balance": 450000.50,
  "month_revenue": 1200000.00,
  "month_expenses": 800000.00,
  "recent_transactions": [...],
  "outstanding_invoices": {
    "pending": 250000.00,
    "overdue": 50000.00
  },
  "latest_forecast": {...},
  "anomaly_score": 0.02  # Low score = normal, high = suspicious
}
```

### 6. **Regulatory Risk Monitoring** (Framework Ready)

Monitor regulatory and compliance risks:

**Planned Features**:
- BSE filing scraping for listed companies
- Promoter pledge data extraction
- Auditor opinion analysis via NLP
- Anomaly detection using Isolation Forest
- Neo4j graph database for entity relationship mapping

### 7. **Company Watchlist**

Monitor specific companies and their regulatory status:

**Features**:
- Add/remove companies from watchlist
- Track BSE codes for listed companies
- Monitor regulatory filings and changes
- Set alerts for compliance events

**Example**:
```bash
POST /api/watchlist/add
{
  "business_id": 1,
  "company_name": "Reliance Industries",
  "bse_code": "RIL",
  "gstin": "27AABDU1234F1Z0"
}
```

### 8. **User Authentication & Authorization**

Secure, JWT-based authentication system:

**Features**:
- User registration with email and password (bcrypt hashing)
- JWT token-based authentication (60-minute expiry by default)
- Business association (multi-tenant support)
- User profile management

**Example**:
```bash
# Register
POST /api/auth/register
{
  "email": "user@example.com",
  "password": "secure_password",
  "full_name": "John Doe",
  "business_name": "ABC Enterprises"
}

# Login
POST /api/auth/login
{
  "email": "user@example.com",
  "password": "secure_password"
}

# Response
{
  "access_token": "eyJhbGciOiJIUzI1NiI...",
  "token_type": "bearer",
  "user": {...}
}
```

### 9. **Asynchronous Background Processing**

Celery-powered task queue for long-running operations:

**Use Cases**:
- File parsing (large Tally XML files)
- Data deduplication across thousands of records
- ML model training and inference
- Batch report generation

**Example Background Task**:
```bash
# Upload triggers async task
POST /api/data/upload → background task processing

# Check task status
GET /api/data/upload-status/{task_id}

Response:
{
  "task_id": "abc-123",
  "status": "processing",
  "percent": 65,
  "message": "Processing 1500 transactions...",
  "records_added": 1050
}
```

### 10. **Knowledge Graph & Entity Relationships**

Neo4j graph database for complex entity relationships:

**Capabilities**:
- Map client-to-client relationships (who pays whom)
- Identify key business relationships
- Supply chain mapping
- Risk contagion analysis (if one client defaults, who else is affected?)

**Example Graph Queries**:
```cypher
# Find all transactions between two businesses
MATCH (b1:Business)-[:PAID_TO]->(b2:Business)
WHERE b1.id = 1 AND b2.id = 2
RETURN b1, b2, count(*) as transaction_count

# Find payment chains (supply chain)
MATCH path = (b1:Business)-[:PAID_TO*2..4]->(b2:Business)
WHERE b1.id = 1
RETURN path
```

### 11. **Vector Search & Similarity Matching**

Qdrant vector database for semantic search:

**Applications**:
- Find similar transactions for pattern detection
- Fraud detection by finding anomalous transaction patterns
- Client clustering by spending behavior
- Recommended business contacts

**Example**:
```bash
POST /api/search/similar-transactions
{
  "transaction_id": 12345,
  "top_k": 10  # Return 10 most similar transactions
}
```

---

## Project Structure

```
Finemonix/
├── backend/                    # FastAPI backend application
│   ├── routers/               # API route handlers
│   ├── services/              # Business logic (parsers, entity resolution, etc.)
│   ├── ml/                    # Machine learning models (LSTM, Prophet)
│   ├── tasks/                 # Celery async tasks
│   ├── schemas/               # Request/response schemas
│   ├── models.py              # SQLAlchemy ORM models
│   ├── database.py            # Database connection setup
│   ├── config.py              # Configuration management
│   ├── main.py                # FastAPI application entry point
│   ├── requirements.txt        # Python dependencies
│   └── alembic/               # Database migrations
├── frontend/                   # Next.js React frontend
│   ├── app/                   # Next.js app directory
│   ├── components/            # React components
│   ├── lib/                   # Utilities and libraries
│   └── package.json           # NPM dependencies
├── docker/                    # Docker configurations
│   ├── Dockerfile.api         # FastAPI application Docker image
│   └── Dockerfile.worker      # Celery worker Docker image
├── db/                        # Database schema and scripts
├── ml/                        # Machine learning pipelines
├── scripts/                   # Utility and setup scripts
│   └── smoke_test.py          # End-to-end loan module smoke test (NBFC pitch sequence)
├── tests/                     # Test suite
├── docker-compose.yml         # Docker Compose orchestration
└── .env                       # Environment variables (create this)
```

---

## Prerequisites

### System Requirements
- **OS**: Windows, macOS, or Linux
- **Python**: 3.11 or higher
- **Node.js**: 18.x or higher
- **Docker & Docker Compose**: Latest stable versions
- **RAM**: Minimum 4GB (8GB+ recommended for ML operations)

### Software to Install
1. **Python 3.11+** — [Download](https://www.python.org/downloads/)
2. **Node.js 18+** — [Download](https://nodejs.org/)
3. **Docker Desktop** — [Download](https://www.docker.com/products/docker-desktop)
4. **Git** — [Download](https://git-scm.com/)

---

## Environment Setup

### Step 1: Create Environment Variables File

Create a `.env` file in the project root with the following variables:

```bash
# Database Configuration
POSTGRES_USER=finemonix_user
POSTGRES_PASSWORD=your_secure_password_here
POSTGRES_DB=finemonix_db
DATABASE_URL=postgresql+asyncpg://finemonix_user:your_secure_password_here@localhost:5432/finemonix_db

# Redis Configuration
REDIS_URL=redis://localhost:6379

# Neo4j Graph Database
NEO4J_URI=neo4j://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_neo4j_password_here

# Qdrant Vector Database
QDRANT_URL=http://localhost:6333

# Application Settings
SECRET_KEY=your_secret_key_here_minimum_32_characters_long
DEBUG=development
```

**Important**: Never commit the `.env` file to version control. Keep it secure!

---

## Quick Start (Recommended)

This is the easiest way to get everything running with Docker Compose.

### Terminal 1: Start All Services with Docker Compose

```bash
# Navigate to project root
cd Finemonix

# Start all infrastructure services (PostgreSQL, Redis, Neo4j, Qdrant) and the API
docker-compose up --build

# Expected output:
# - postgres is ready for connections
# - redis is accepting connections
# - neo4j is ready
# - qdrant is listening
# - Finemonix API starting on http://0.0.0.0:8000
```

The system will be fully initialized and ready to use. Access the API at `http://localhost:8000/docs`

---

## Manual Setup

If you prefer to run services individually without Docker, follow these steps:

### Step 1: Start Infrastructure Services (Docker)

Open a new terminal and run:

```bash
# Start only the infrastructure services
docker-compose up -d postgres redis neo4j qdrant

# Verify services are running
docker-compose ps

# Expected services to be healthy:
# - postgres (port 5432)
# - redis (port 6379)
# - neo4j (port 7474, 7687)
# - qdrant (port 6333, 6334)
```

### Step 2: Set Up Python Virtual Environment

```bash
# Create a virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate

# Verify activation (should show venv in prompt)
```

### Step 3: Install Python Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install backend requirements
cd backend
pip install -r requirements.txt

# Return to project root
cd ..
```

### Step 4: Set Up Database

```bash
# Initialize database migrations (if needed)
cd backend
alembic upgrade head

# Return to project root
cd ..
```

### Step 5: Install Frontend Dependencies

```bash
# Navigate to frontend
cd frontend

# Install Node.js dependencies
npm install

# Return to project root
cd ..
```

---

## Running the System

Once setup is complete, you need to run multiple services. **Each service runs in its own terminal**.

### Backend API (Terminal 1)

```bash
# Activate Python environment (if not already active)
venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux

# Start FastAPI development server with auto-reload
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Expected output:
# Uvicorn running on http://0.0.0.0:8000
# Press CTRL+C to quit
```

**API will be available at**: `http://localhost:8000`

### Frontend Application (Terminal 2)

```bash
# Navigate to frontend directory
cd frontend

# Start Next.js development server
npm run dev

# Expected output:
# Ready in X.XXs
# Local: http://localhost:3000
# Press q to stop
```

**Frontend will be available at**: `http://localhost:3000`

### Celery Worker (Terminal 3) - For Background Tasks

```bash
# Activate Python environment
venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux

# Start Celery worker
cd backend
celery -A tasks.celery_app worker --loglevel=info

# Expected output:
# Celery is starting...
# ready to accept tasks
```

**Optional - Purge Task Queue** (use before starting worker if queue has stale tasks):

```bash
cd backend
celery -A tasks.celery_app purge -f
# Confirms and purges all pending tasks
```

**Optional - Monitor Celery Tasks**, open another terminal:

```bash
# Terminal 4: Monitor Celery tasks
venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux

cd backend
celery -A tasks.celery_app events

# or use Celery Flower for a web UI
celery -A tasks.celery_app flower

# Access Flower at: http://localhost:5555
```

---

## API Documentation

### Interactive API Docs (Swagger UI)

```
http://localhost:8000/docs
```

### Alternative API Docs (ReDoc)

```
http://localhost:8000/redoc
```

### Available API Endpoints

#### Authentication
- `POST /api/auth/register` — Register a new user
- `POST /api/auth/login` — Login user
- `POST /api/auth/logout` — Logout user

#### Data Management
- `POST /api/data/upload` — Upload financial data
- `GET /api/data/files` — List uploaded files
- `POST /api/data/parse` — Parse uploaded documents

#### Forecasting
- `POST /api/forecast/cashflow` — Generate 90-day cash flow forecast
- `GET /api/forecast/history` — Get forecast history

#### Loan Analysis
- `POST /api/loan/eligibility` — Check loan eligibility across all lender types (PSU / NBFC / Private / MFI)
- `POST /api/loan/whatif` — O(1) what-if delta on SHAP decomposition (~5ms)
- `GET /api/loan/report/{entity_id}` — Get full loan analysis report with SHAP waterfall

#### Watchlist
- `POST /api/watchlist/add` — Add company to watchlist
- `GET /api/watchlist/companies` — Get watchlist

#### Dashboard
- `GET /api/dashboard/overview` — Get dashboard overview
- `GET /api/dashboard/metrics` — Get key metrics

#### Health Check
- `GET /api/health` — API health status

---

## How Features Work Together: Complete Example Flow

Here's how the features integrate to deliver complete financial intelligence:

### Scenario: Onboarding a New Business and Generating Forecast

**Step 1: User Registration**
```bash
POST /api/auth/register
{
  "email": "founder@abcenterprises.com",
  "password": "secure_pass",
  "full_name": "Amit Patel",
  "business_name": "ABC Enterprises"
}
```
✅ User account created + Business record initialized

**Step 2: Upload Tally Export**
```bash
# Get last year's Tally export
POST /api/data/upload
Content-Type: multipart/form-data

business_id=1&file_type=tally&file=Tally_Export_2025.xml
```
✅ File saved to temp storage
✅ Celery background task queued
✅ Returns task_id for progress tracking

**Step 3: Async Processing (happens in background)**
- Tally XML parsed → Extracts 15,000 transactions
- Transactions deduplicated → Reduces to 12,000 unique transactions
- Clients identified → 450 unique clients extracted
- Entity resolution → Fuzzy matched to canonical entities (ABC Corp, ABC Enterprises Ltd → ABC Enterprises)
- Data stored in PostgreSQL

**Step 4: Check Progress**
```bash
GET /api/data/upload-status/task-abc-123

{
  "status": "processing",
  "percent": 75,
  "message": "Running entity resolution...",
  "records_added": 9800
}
```

**Step 5: Upload GST and Bank Data**
```bash
# Upload GST invoices
POST /api/data/upload
business_id=1&file_type=gst&file=GST_Invoices_2025.json

# Upload bank statement
POST /api/data/upload
business_id=1&file_type=bank&file=Bank_Statement_2025.csv
```
✅ Data automatically deduplicated against existing Tally records

**Step 6: Generate Cash Flow Forecast**
```bash
POST /api/forecast/cashflow
{
  "business_id": 1,
  "days_ahead": 90,
  "operating_threshold": 100000  # Red flag if balance falls below 1L
}
```

Backend Processing:
1. Retrieves all transactions from last 90 days
2. Builds features (running balance, daily net flow, etc.)
3. Runs LSTM model with MC Dropout → Get p10, p50, p90 predictions
4. Runs Prophet model → Get seasonal forecast
5. Ensemble blend both predictions (60% LSTM + 40% Prophet)
6. Identifies danger zones where p10 < threshold
7. Caches result in Redis

**Response**:
```json
{
  "forecast": [
    {
      "forecast_date": "2026-06-15",
      "predicted_balance": 250000.00,
      "p10_balance": 180000.00,
      "p90_balance": 320000.00,
      "model_version": "1.0"
    }
  ],
  "danger_zones": [
    {
      "start_date": "2026-07-10",
      "end_date": "2026-07-15",
      "min_balance": 75000.00,
      "shortfall": 25000.00,
      "severity": "high"
    }
  ],
  "generated_at": "2026-06-02T10:30:00Z"
}
```

**Step 7: View Dashboard**
```bash
GET /api/dashboard/1

{
  "business": {"id": 1, "name": "ABC Enterprises", "quality_score": 92},
  "current_balance": 450000.50,
  "month_revenue": 1200000.00,
  "month_expenses": 800000.00,
  "outstanding_invoices": {
    "pending": 250000.00,
    "overdue": 50000.00
  }
}
```

**Step 8: Check Loan Eligibility (Multi-Lender + What-If)**
```bash
POST /api/loan/eligibility
{
  "business_id": 1,
  "delay_days": 30,
  "amount_override": null
}
```

**Response**:
```json
{
  "lenders": {
    "psu":     { "probability": 0.28, "eligible": false },
    "nbfc":    { "probability": 0.71, "eligible": true },
    "private": { "probability": 0.54, "eligible": true },
    "mfi":     { "probability": 0.88, "eligible": true }
  },
  "shap_explanation": {
    "base_value": 0.45,
    "features": [
      { "name": "client_concentration", "shap_value": -0.18 },
      { "name": "revenue_stability",    "shap_value": +0.21 }
    ]
  },
  "response_ms": 22
}
```

**Step 9: What-If Scenario (reduce client concentration)**
```bash
POST /api/loan/whatif
{
  "business_id": 1,
  "feature_overrides": { "client_concentration": 0.40 }
}
# NBFC probability climbs from 0.71 → ~0.81 in <5ms
```

---

## Detailed API Endpoints Reference

### Authentication Endpoints

#### Register User
```bash
POST /api/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "secure_password_123",
  "full_name": "John Doe",
  "business_name": "My Business"
}

Response (201 Created):
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "John Doe",
  "business_id": 1
}
```

#### Login User
```bash
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "secure_password_123"
}

Response (200 OK):
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Data Management Endpoints

#### Upload Financial Data
```bash
POST /api/data/upload
Content-Type: multipart/form-data

business_id: 1
file_type: tally|gst|bank
file: <binary file>

Response (202 Accepted):
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "queued"
}
```

#### Get Upload Progress
```bash
GET /api/data/upload-status/{task_id}

Response (200 OK):
{
  "status": "processing",
  "percent": 65,
  "message": "Processing 1500 transactions...",
  "records_added": 1050
}
```

### Forecasting Endpoints

#### Generate Cash Flow Forecast
```bash
POST /api/forecast/cashflow
Content-Type: application/json

{
  "business_id": 1,
  "days_ahead": 90,
  "operating_threshold": 100000.00
}

Response (200 OK):
{
  "forecast": [
    {
      "forecast_date": "2026-06-03",
      "predicted_balance": 450000.50,
      "p10_balance": 380000.00,
      "p90_balance": 520000.00
    }
  ],
  "danger_zones": [...]
}
```

### Dashboard Endpoints

#### Get Dashboard Summary
```bash
GET /api/dashboard/{business_id}

Response (200 OK):
{
  "business": {
    "id": 1,
    "name": "ABC Enterprises",
    "quality_score": 92
  },
  "current_balance": 450000.50,
  "month_revenue": 1200000.00,
  "month_expenses": 800000.00,
  "outstanding_invoices": {
    "pending": 250000.00,
    "overdue": 50000.00
  }
}
```

### Loan Analysis Endpoints

#### Check Loan Eligibility
```bash
POST /api/loan/eligibility
Content-Type: application/json

{
  "business_id": 1,
  "delay_days": 0,
  "amount_override": null
}

Response (200 OK):
{
  "lenders": {
    "psu":     { "probability": 0.28, "eligible": false },
    "nbfc":    { "probability": 0.71, "eligible": true },
    "private": { "probability": 0.54, "eligible": true },
    "mfi":     { "probability": 0.88, "eligible": true }
  },
  "shap_explanation": { "base_value": 0.45, "features": [...] },
  "response_ms": 22
}
```

#### What-If Loan Scenario (O(1) Delta Engine)
```bash
POST /api/loan/whatif
Content-Type: application/json

{
  "business_id": 1,
  "feature_overrides": {
    "client_concentration": 0.40,
    "avg_payment_delay_days": 15
  }
}

Response (200 OK):
{
  "lenders": {
    "nbfc": { "probability": 0.81, "delta": +0.10 }
  },
  "response_ms": 5
}
```

### Watchlist Endpoints

#### Add Company to Watchlist
```bash
POST /api/watchlist/add
Content-Type: application/json

{
  "business_id": 1,
  "company_name": "Reliance Industries",
  "bse_code": "RIL"
}

Response (201 Created):
{
  "id": 1,
  "company_name": "Reliance Industries",
  "bse_code": "RIL"
}
```

#### Get Watchlist
```bash
GET /api/watchlist/companies?business_id=1

Response (200 OK):
{
  "companies": [
    {
      "id": 1,
      "company_name": "Reliance Industries",
      "bse_code": "RIL"
    }
  ]
}
```

### Health Check Endpoint

#### API Health Status
```bash
GET /api/health

Response (200 OK):
{
  "status": "healthy",
  "version": "1.0",
  "database": "connected",
  "redis": "connected",
  "timestamp": "2026-06-02T10:30:00Z"
}
```

---

## Development Workflow

### Database Migrations with Alembic

When you modify database models, create migrations:

```bash
# Activate Python environment
venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux

cd backend

# Create a new migration (auto-generates from model changes)
alembic revision --autogenerate -m "Add new_column to users table"

# Review the generated migration file in alembic/versions/

# Apply migration to database
alembic upgrade head

# Downgrade one migration if needed
alembic downgrade -1

# View migration history
alembic history
```

### Running Tests

```bash
# Activate Python environment
venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux

# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_forecast.py

# Run with verbose output
pytest -v tests/

# Run with coverage report
pytest --cov=backend tests/
```

### Linting and Code Quality (Frontend)

```bash
cd frontend

# Run ESLint
npm run lint

# Fix linting issues automatically
npm run lint -- --fix
```

### Building for Production

#### Backend

```bash
# Build Docker image for API
docker build -f docker/Dockerfile.api -t finemonix-api:latest .

# Build Docker image for Celery worker
docker build -f docker/Dockerfile.worker -t finemonix-worker:latest .
```

#### Frontend

```bash
cd frontend

# Build Next.js for production
npm run build

# Start production server
npm start
```

---

## Common Commands Summary

### Docker Commands

```bash
# Start all services
docker-compose up --build

# Start services in background
docker-compose up -d

# Stop services
docker-compose down

# Stop and remove volumes (careful - deletes data!)
docker-compose down -v

# View service logs
docker-compose logs -f [service_name]

# View specific service logs
docker-compose logs -f postgres  # PostgreSQL logs
docker-compose logs -f redis     # Redis logs
docker-compose logs -f neo4j     # Neo4j logs
docker-compose logs -f qdrant    # Qdrant logs
```

### Database Commands

```bash
# Access PostgreSQL CLI
docker-compose exec postgres psql -U finemonix_user -d finemonix_db

# Common SQL commands:
\dt                    # List tables
\d users              # Describe users table
SELECT * FROM users;  # Query users
\q                    # Exit PostgreSQL
```

### Python Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (macOS/Linux)
source venv/bin/activate

# Deactivate
deactivate

# Install packages
pip install package_name

# List installed packages
pip list

# Save dependencies
pip freeze > requirements.txt
```

### Frontend Commands

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Start production server
npm start

# Run linter
npm run lint
```

---

## Troubleshooting

### Docker Services Won't Start

```bash
# Check if ports are in use
# Windows:
netstat -ano | findstr :5432

# macOS/Linux:
lsof -i :5432

# Kill process on port
# Windows:
taskkill /PID <PID> /F

# macOS/Linux:
kill -9 <PID>
```

### PostgreSQL Connection Issues

```bash
# Check if PostgreSQL is running
docker-compose ps

# Restart PostgreSQL
docker-compose restart postgres

# Check PostgreSQL logs
docker-compose logs postgres
```

### Redis Connection Issues

```bash
# Test Redis connection
docker-compose exec redis redis-cli ping

# Should return: PONG
```

### Frontend Port 3000 Already in Use

```bash
# Run on different port
npm run dev -- -p 3001
```

### Backend Port 8000 Already in Use

```bash
# Run on different port
uvicorn backend.main:app --host 0.0.0.0 --port 8001 --reload
```

### Module Import Errors

```bash
# Reinstall dependencies (in backend)
pip install --upgrade --force-reinstall -r requirements.txt
```

### Celery Worker Issues

#### Purge All Queued Tasks

If you need to clear all pending Celery tasks from the queue (useful for development or debugging):

```bash
# From backend directory
cd backend
celery -A tasks.celery_app purge -f

# Or from workspace root
celery -A backend.tasks.celery_app purge -f

# Expected output:
# WARNING: This will remove all tasks from the queue!
# Type 'yes' to confirm...
# yes
# Queue purged successfully
```

#### Start Celery Worker

```bash
# From backend directory
cd backend
celery -A tasks.celery_app worker --loglevel=info

# Or from workspace root
celery -A backend.tasks.celery_app worker --loglevel=info

# Expected output:
# - Starting Celery worker...
# - Connected to redis://localhost:6379
# - Ready to accept tasks
```

#### Monitor Celery Tasks

```bash
# Option 1: Real-time task events
cd backend
celery -A tasks.celery_app events

# Option 2: Celery Flower (Web UI - recommended)
cd backend
celery -A tasks.celery_app flower

# Access Flower dashboard at: http://localhost:5555
```

### Clear Everything and Start Fresh

```bash
# Stop and remove all containers and volumes
docker-compose down -v

# Remove virtual environment
rmdir /s venv  # Windows
rm -rf venv    # macOS/Linux

# Remove node_modules
rmdir /s frontend\node_modules  # Windows
rm -rf frontend/node_modules    # macOS/Linux

# Then follow setup instructions from the beginning
```

---

## System Architecture

### Technology Stack

**Backend:**
- **Framework**: FastAPI (Python)
- **Database**: PostgreSQL (relational data)
- **Cache**: Redis (session, caching)
- **Graph DB**: Neo4j (entity relationships)
- **Vector DB**: Qdrant (embeddings, similarity search)
- **Task Queue**: Celery (async task processing)

**Frontend:**
- **Framework**: Next.js 16 (React 19)
- **Styling**: Tailwind CSS 4
- **Authentication**: NextAuth.js
- **Charts**: Chart.js

**ML/Data:**
- **Forecasting**: Prophet + LSTM (PyTorch)
- **Loan Eligibility**: XGBoost + SHAP
- **NLP**: spaCy, RapidFuzz
- **Data Processing**: Pandas, NumPy, Scikit-learn
- **PDF Processing**: pdfplumber, Tesseract OCR

### Data Flow

1. **Data Ingestion** → Upload Tally XML, GST JSON, Bank CSV
2. **Parsing & Cleaning** → Parse files, deduplicate, resolve entities
3. **ML Processing** → Generate forecasts, check loan eligibility, detect risks
4. **Storage** → Save to PostgreSQL, Neo4j, Qdrant
5. **API Response** → Return results via REST API
6. **Frontend Visualization** → Display in dashboard

---

## Performance Optimization Tips

1. **Increase Python Memory for ML Operations**: Set environment variable before running
   ```bash
   # Windows
   set PYTHONUNBUFFERED=1
   
   # macOS/Linux
   export PYTHONUNBUFFERED=1
   ```

2. **Optimize Frontend Build**: 
   ```bash
   npm run build  # Optimizes bundle size
   ```

3. **Database Indexing**: Ensure indexes are created for frequently queried columns

4. **Redis Caching**: API responses are cached in Redis for faster retrieval

---

## Contributing

When contributing to Finemonix:

1. Create a new branch: `git checkout -b feature/your-feature`
2. Make your changes
3. Run tests: `pytest tests/`
4. Commit: `git commit -am "Description of changes"`
5. Push: `git push origin feature/your-feature`
6. Create a Pull Request

---

## Data Models & Database Schema

### Core Data Models

**Business**
```python
{
  "id": int,
  "name": str,
  "gstin": str (optional),        # GST registration number
  "pan": str (optional),          # PAN number
  "business_type": str,           # e.g., "Manufacturing", "Trade"
  "onboarding_date": date,
  "data_sources_connected": List[str],  # ["tally", "gst", "bank"]
  "quality_score": int,           # 0-100 based on data quality
  "safety_threshold_inr": float,  # Cash balance threshold for alerts
  "opening_balance": float        # Starting cash balance
}
```

**User**
```python
{
  "id": int,
  "email": str (unique),
  "hashed_password": str,         # bcrypt hashed
  "full_name": str,
  "business_id": int (FK),
  "created_at": datetime
}
```

**Client (Entity)**
```python
{
  "id": int,
  "business_id": int (FK),
  "canonical_name": str,          # Deduplicated name
  "gstin": str (optional),        # GST number
  "is_listed_company": bool,
  "bse_code": str (optional),
  "total_revenue_share": float,   # % of total revenue
  "avg_payment_delay_days": int,  # Average payment delay
  "aliases": List[str],           # Alternative names found in data
  "created_at": datetime
}
```

**Transaction**
```python
{
  "id": int,
  "business_id": int (FK),
  "date": date,
  "amount": float,
  "direction": str,               # "in" or "out"
  "category": str (optional),     # "Sales", "Expense", etc.
  "counterparty_id": int (FK),    # Client involved
  "source": str,                  # "tally", "gst", or "bank"
  "raw_description": str,
  "created_at": datetime
}
```

**Invoice**
```python
{
  "id": int,
  "business_id": int (FK),
  "client_id": int (FK),
  "amount": float,
  "issue_date": date,
  "due_date": date,
  "paid_date": date (optional),
  "status": str,                  # "pending", "paid", "overdue", "partial"
  "days_overdue": int (optional),
  "source": str                   # "manual" or import source
}
```

**CashFlowForecast**
```python
{
  "id": int,
  "business_id": int (FK),
  "generated_at": datetime,
  "forecast_date": date,
  "predicted_balance": float,     # Point estimate
  "p10_balance": float,           # Pessimistic (10th percentile)
  "p90_balance": float,           # Optimistic (90th percentile)
  "model_version": str,           # e.g., "1.0"
  "model_used": str               # "lstm", "prophet", or "hybrid"
}
```

**DataImportJob**
```python
{
  "id": int,
  "business_id": int (FK),
  "task_id": str (unique),        # Celery task ID
  "file_type": str,               # "tally", "gst", or "bank"
  "filename": str,
  "status": str,                  # "queued", "processing", "completed", "failed"
  "percent": int (0-100),
  "message": str,
  "records_added": int,
  "error_message": str (optional),
  "result": dict (JSON),
  "created_at": datetime,
  "completed_at": datetime (optional)
}
```

---

## Key Implementation Details

### 1. Tally Parser - Multi-Currency Handling

The Tally parser automatically detects and converts foreign currencies to INR:

```python
# Supported currencies with hardcoded exchange rates
USD → 83.0 INR
EUR → 90.0 INR
GBP → 105.0 INR
```

Example: `"$ 100"` in Tally → Converts to `₹ 8300`

### 2. Entity Resolution Algorithm

Three-pass entity matching strategy:

**Pass 1: GSTIN Authority** (Most reliable)
- If GSTIN matches → Entity found
- Add as new alias if name is different

**Pass 2: Fuzzy String Matching** (RapidFuzz)
- Compare new name against all existing aliases
- Threshold: 85% token sort ratio
- Handles typos and spacing variations

**Pass 3: Semantic Similarity** (Sentence Transformers)
- Uses "all-MiniLM-L6-v2" embedding model
- Cosine similarity threshold: 0.85
- Handles contextual name variations

**Example**:
```
"ABC Enterprises" vs "ABC Enterprises Pvt Ltd"
→ Token sort ratio: 87% → MATCH
```

### 3. LSTM Forecasting Architecture

```
Input Layer (N features)
    ↓
LSTM Layer 1 (128 units, Dropout=0.3)
    ↓
LSTM Layer 2 (128 units, Dropout=0.3)
    ↓
Dense Layer (90 outputs - one per day)
    ↓
Output: [day1_forecast, day2_forecast, ..., day90_forecast]
```

**MC Dropout Uncertainty**: Run inference 30-50 times with dropout enabled:
- p10 = 10th percentile of predictions
- p50 = 50th percentile (median)
- p90 = 90th percentile

### 4. Prophet Model Components

```
Time Series = Trend + Seasonality + Holiday Effects + Regressors

Seasonality:
  - Weekly (period=7, fourier=3)
  - Monthly (period=30.5, fourier=5)

Regressors:
  - is_gst_filing_day: 1 if day ±2 of 20th
  - future_invoices: Expected revenue
```

### 5. Dashboard Calculations

**Current Balance** (Real-time):
```sql
SUM(CASE 
  WHEN direction='in' THEN amount 
  ELSE -amount 
END)
```

**Monthly Metrics**:
```sql
-- Current month starts from 1st
Month_Revenue = SUM(amount) WHERE direction='in' AND date >= month_start
Month_Expense = SUM(amount) WHERE direction='out' AND date >= month_start
```

**Outstanding Invoices**:
```sql
Pending = SUM(amount) WHERE status='pending'
Overdue = SUM(amount) WHERE status='overdue'
```

---

## Feature Implementation Status

> **Last synced with codebase**: June 14, 2026 (Day 18 of 30)

| Feature | Status | Details |
|---------|--------|---------|
| User Authentication | ✅ Complete | JWT-based with bcrypt hashing |
| Tally Parser | ✅ Complete | Multi-currency, complex voucher handling |
| GST Parser | ✅ Complete | JSON parsing, GSTIN extraction |
| Bank Parser | ✅ Complete | CSV parsing, statement reconciliation |
| Entity Resolution | ✅ Complete | GSTIN + Fuzzy + Embeddings (3-pass) |
| Transaction Deduplication | ✅ Complete | Date, amount, counterparty matching |
| LSTM Forecasting | ✅ Complete | MC Dropout, net-delta target, cumsum anchor |
| Prophet Forecasting | ✅ Complete | Seasonal decomposition, GST regressor |
| Danger Zone Detection | ✅ Complete | Contiguous period identification |
| Dashboard (frontend) | ✅ Complete | Real-time metrics, frontend tab wired |
| Cash Flow Tab (frontend) | ✅ Complete | 90-day area chart, scenario sidebar |
| Integration Tab (frontend) | ✅ Complete | Data sources, upload status |
| Invoice Tracking | ✅ Complete | Status tracking, overdue calculation |
| Loan Eligibility Engine | ✅ Complete | XGBoost + SHAP, calibrated per lender type (PSU / NBFC / Private / MFI) |
| SHAP What-If Delta Engine | ✅ Complete | O(1) additive delta, sub-25ms response, Redis-cached decomposition |
| Loan Tab (frontend) | ✅ Complete | Eligibility gauges, SHAP waterfall, what-if CTA wired to forecast API |
| Loan Integration Tests | ✅ Complete | Full NBFC pitch-sequence fixture, smoke test script |
| Watchlist | ✅ Complete | Company monitoring setup |
| Neo4j Integration | ⚠️ Ready | Framework prepared, schema defined |
| Qdrant Vector Search | ⚠️ Ready | Infrastructure in place |
| Regulatory Monitoring | 📋 Planned | BSE scraping, NLP analysis, Isolation Forest anomaly detection |
| Company Knowledge Graph | 📋 Planned | D3 force graph, Neo4j GDS, pledge tracker |

---

## Support & Documentation

For detailed API documentation, see `http://localhost:8000/docs` (when API is running)

For frontend development, check `frontend/README.md`

---

## License

[Add your license information here]

---

**Last Updated**: June 14, 2026 (Day 18 / 30)
**Project Version**: 1.0
**Status**: Active Development — Loan module complete, Regulatory Monitor next