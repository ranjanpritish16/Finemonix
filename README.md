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

### 4. **Loan Eligibility & Risk Assessment**

Finemonix provides intelligent loan eligibility analysis (framework prepared, models trainable):

**Features**:
- XGBoost classifier calibration for loan approval prediction
- SHAP (SHapley Additive exPlanations) for explainable AI
- Sub-100ms response time for what-if analysis
- Scenario testing: Adjust payment delays and revenue to see impact on eligibility

**Example Scenario Request**:
```bash
POST /api/loan/eligibility
{
  "business_id": 1,
  "client_id": 5,
  "delay_days": 30,        # What if payments are delayed 30 days?
  "amount_override": 500000 # What if revenue drops to 500k?
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

**Optional**: If you want to monitor Celery tasks, open another terminal:

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
- `POST /api/loan/eligibility` — Check loan eligibility
- `GET /api/loan/report/{entity_id}` — Get loan analysis report

#### Watchlist
- `POST /api/watchlist/add` — Add company to watchlist
- `GET /api/watchlist/companies` — Get watchlist

#### Dashboard
- `GET /api/dashboard/overview` — Get dashboard overview
- `GET /api/dashboard/metrics` — Get key metrics

#### Health Check
- `GET /api/health` — API health status

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

## Support & Documentation

For detailed API documentation, see `http://localhost:8000/docs` (when API is running)

For frontend development, check `frontend/README.md`

---

## License

[Add your license information here]

---

**Last Updated**: June 2, 2026
**Project Version**: 1.0
**Status**: Active Development
