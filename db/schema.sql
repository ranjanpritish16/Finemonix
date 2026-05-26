-- =============================================================================
-- Finemonix — PostgreSQL Schema
-- Run: psql -d finemonix_db -f db/schema.sql
-- =============================================================================

-- 1. businesses
--    Core tenant table. Every upload, forecast, and loan check belongs to one.
CREATE TABLE IF NOT EXISTS businesses (
    id                      SERIAL          PRIMARY KEY,
    name                    VARCHAR(255)    NOT NULL,
    gstin                   VARCHAR(15)     UNIQUE,
    pan                     VARCHAR(10),
    business_type           VARCHAR(50),
    onboarding_date         DATE            DEFAULT CURRENT_DATE,
    data_sources_connected  JSONB           DEFAULT '[]',
    quality_score           INTEGER         DEFAULT 0,
    safety_threshold_inr    DECIMAL(15,2)   DEFAULT 50000,
    created_at              TIMESTAMPTZ     DEFAULT NOW()
);

-- 2. users
--    User credentials and access management.
CREATE TABLE IF NOT EXISTS users (
    id                      SERIAL          PRIMARY KEY,
    business_id             INTEGER         REFERENCES businesses(id) ON DELETE SET NULL,
    email                   VARCHAR(255)    UNIQUE NOT NULL,
    hashed_password         VARCHAR(255)    NOT NULL,
    full_name               VARCHAR(255),
    created_at              TIMESTAMPTZ     DEFAULT NOW()
);

-- 3. clients
--    Resolved counterparty entities linked to a business.
CREATE TABLE IF NOT EXISTS clients (
    id                      SERIAL          PRIMARY KEY,
    business_id             INTEGER         NOT NULL
                                REFERENCES businesses(id) ON DELETE CASCADE,
    canonical_name          VARCHAR(255)    NOT NULL,
    gstin                   VARCHAR(15),
    is_listed_company       BOOLEAN         DEFAULT FALSE,
    bse_code                VARCHAR(20),
    total_revenue_share     DECIMAL(5,2)    DEFAULT 0,
    avg_payment_delay_days  INTEGER         DEFAULT 0,
    aliases                 JSONB           DEFAULT '[]',
    created_at              TIMESTAMPTZ     DEFAULT NOW()
);

-- 4. transactions
--    Every financial event ingested from Tally / GST / Bank CSV.
CREATE TABLE IF NOT EXISTS transactions (
    id                  SERIAL          PRIMARY KEY,
    business_id         INTEGER         NOT NULL
                            REFERENCES businesses(id) ON DELETE CASCADE,
    date                DATE            NOT NULL,
    amount              DECIMAL(15,2)   NOT NULL,
    direction           VARCHAR(3)      NOT NULL
                            CHECK (direction IN ('in', 'out')),
    category            VARCHAR(100),
    counterparty_id     INTEGER
                            REFERENCES clients(id) ON DELETE SET NULL,
    source              VARCHAR(10)     NOT NULL
                            CHECK (source IN ('tally', 'gst', 'bank')),
    raw_description     TEXT,
    created_at          TIMESTAMPTZ     DEFAULT NOW()
);

-- 5. invoices
--    Sales and purchase invoices extracted from GST/Tally data.
CREATE TABLE IF NOT EXISTS invoices (
    id              SERIAL          PRIMARY KEY,
    business_id     INTEGER         NOT NULL
                        REFERENCES businesses(id) ON DELETE CASCADE,
    client_id       INTEGER
                        REFERENCES clients(id) ON DELETE SET NULL,
    amount          DECIMAL(15,2)   NOT NULL,
    issue_date      DATE            NOT NULL,
    due_date        DATE            NOT NULL,
    paid_date       DATE,
    status          VARCHAR(20)     DEFAULT 'pending'
                        CHECK (status IN ('pending', 'paid', 'overdue', 'partial')),
    days_overdue    INTEGER
);

-- 6. cash_flow_forecasts
--    Stores per-day LSTM/Prophet predictions (p10 / median / p90).
CREATE TABLE IF NOT EXISTS cash_flow_forecasts (
    id                  SERIAL          PRIMARY KEY,
    business_id         INTEGER         NOT NULL
                            REFERENCES businesses(id) ON DELETE CASCADE,
    generated_at        TIMESTAMPTZ     DEFAULT NOW(),
    forecast_date       DATE            NOT NULL,
    predicted_balance   DECIMAL(15,2),
    p10_balance         DECIMAL(15,2),
    p90_balance         DECIMAL(15,2),
    model_version       VARCHAR(20),
    model_used          VARCHAR(10)
);

-- 7. companies_watched
--    BSE codes/companies watched by businesses for regulatory alerts.
CREATE TABLE IF NOT EXISTS companies_watched (
    id                  SERIAL          PRIMARY KEY,
    business_id         INTEGER         NOT NULL
                            REFERENCES businesses(id) ON DELETE CASCADE,
    company_bse_code    VARCHAR(20)     NOT NULL,
    company_name        VARCHAR(255)    NOT NULL,
    added_at            TIMESTAMPTZ     DEFAULT NOW(),
    UNIQUE(business_id, company_bse_code)
);

-- 8. filings
--    Regulatory filings metadata and extracted content from BSE.
CREATE TABLE IF NOT EXISTS filings (
    id                  SERIAL          PRIMARY KEY,
    company_bse_code    VARCHAR(20)     NOT NULL,
    filing_type         VARCHAR(50),
    filing_date         DATE            NOT NULL,
    source_url          TEXT,
    raw_text            TEXT,
    extraction_status   VARCHAR(20)     DEFAULT 'pending'
                            CHECK (extraction_status IN ('pending', 'processed', 'failed')),
    extractor_used      VARCHAR(50),
    created_at          TIMESTAMPTZ     DEFAULT NOW()
);

-- 9. anomaly_scores
--    Calculated anomaly scores for quarterly corporate filings.
CREATE TABLE IF NOT EXISTS anomaly_scores (
    id                  SERIAL          PRIMARY KEY,
    company_bse_code    VARCHAR(20)     NOT NULL,
    quarter             VARCHAR(10)     NOT NULL,
    score_financial     DECIMAL(5,2),
    score_tone          DECIMAL(5,2),
    score_graph         DECIMAL(5,2),
    severity            VARCHAR(10)     CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    contributing_features JSONB          DEFAULT '{}',
    created_at          TIMESTAMPTZ     DEFAULT NOW()
);

-- 10. entities
--     Canonical business, person, or auditor entities parsed from filings.
CREATE TABLE IF NOT EXISTS entities (
    id                  SERIAL          PRIMARY KEY,
    canonical_name      VARCHAR(255)    UNIQUE NOT NULL,
    entity_type         VARCHAR(20)     NOT NULL
                            CHECK (entity_type IN ('company', 'person', 'auditor')),
    cin                 VARCHAR(21),
    pan                 VARCHAR(10),
    aliases             JSONB           DEFAULT '[]',
    created_at          TIMESTAMPTZ     DEFAULT NOW()
);

-- 11. entity_aliases
--     Aliases mapping to resolved canonical entities.
CREATE TABLE IF NOT EXISTS entity_aliases (
    id                  SERIAL          PRIMARY KEY,
    entity_id           INTEGER         NOT NULL
                            REFERENCES entities(id) ON DELETE CASCADE,
    alias               VARCHAR(255)    UNIQUE NOT NULL,
    created_at          TIMESTAMPTZ     DEFAULT NOW()
);

-- 12. filing_entities
--     Many-to-many relationship mapping entities mentioned in filings.
CREATE TABLE IF NOT EXISTS filing_entities (
    id                  SERIAL          PRIMARY KEY,
    filing_id           INTEGER         NOT NULL
                            REFERENCES filings(id) ON DELETE CASCADE,
    entity_id           INTEGER         NOT NULL
                            REFERENCES entities(id) ON DELETE CASCADE,
    mention_count       INTEGER         DEFAULT 1,
    created_at          TIMESTAMPTZ     DEFAULT NOW(),
    UNIQUE(filing_id, entity_id)
);

-- =============================================================================
-- Indexes
-- =============================================================================

-- transactions: filtering by business + date range
CREATE INDEX IF NOT EXISTS idx_transactions_business_date
    ON transactions (business_id, date);

-- invoices: client risk scorer and scenario planner filtering by business/client/status
CREATE INDEX IF NOT EXISTS idx_invoices_business_client_status
    ON invoices (business_id, client_id, status);

-- cash_flow_forecasts: dashboard/forecast API queries by business + forecast window
CREATE INDEX IF NOT EXISTS idx_forecasts_business_date
    ON cash_flow_forecasts (business_id, forecast_date);

-- filings: query filings by bse_code and date
CREATE INDEX IF NOT EXISTS idx_filings_bse_date
    ON filings (company_bse_code, filing_date);

-- anomaly_scores: query scores by bse_code and quarter
CREATE INDEX IF NOT EXISTS idx_anomaly_scores_bse_quarter
    ON anomaly_scores (company_bse_code, quarter);

-- entity_aliases: lookup by alias string
CREATE INDEX IF NOT EXISTS idx_entity_aliases_alias
    ON entity_aliases (alias);
