-- =============================================================================
-- FinSentry — PostgreSQL Schema
-- Run: psql -d finsentry_db -f db/schema.sql
-- =============================================================================

-- -----------------------------------------------------------------------------
-- 1. businesses
--    Core tenant table. Every upload, forecast, and loan check belongs to one.
-- -----------------------------------------------------------------------------
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

-- -----------------------------------------------------------------------------
-- 2. clients
--    Resolved counterparty entities linked to a business.
-- -----------------------------------------------------------------------------
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

-- -----------------------------------------------------------------------------
-- 3. transactions
--    Every financial event ingested from Tally / GST / Bank CSV.
-- -----------------------------------------------------------------------------
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
                            REFERENCES clients(id),
    source              VARCHAR(10)     NOT NULL
                            CHECK (source IN ('tally', 'gst', 'bank')),
    raw_description     TEXT,
    created_at          TIMESTAMPTZ     DEFAULT NOW()
);

-- -----------------------------------------------------------------------------
-- 4. invoices
--    Sales and purchase invoices extracted from GST/Tally data.
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS invoices (
    id              SERIAL          PRIMARY KEY,
    business_id     INTEGER         NOT NULL
                        REFERENCES businesses(id) ON DELETE CASCADE,
    client_id       INTEGER
                        REFERENCES clients(id),
    amount          DECIMAL(15,2)   NOT NULL,
    issue_date      DATE            NOT NULL,
    due_date        DATE            NOT NULL,
    paid_date       DATE,
    status          VARCHAR(20)     DEFAULT 'pending'
                        CHECK (status IN ('pending', 'paid', 'overdue', 'partial')),
    days_overdue    INTEGER
);

-- -----------------------------------------------------------------------------
-- 5. cash_flow_forecasts
--    Stores per-day LSTM/Prophet predictions (p10 / median / p90).
-- -----------------------------------------------------------------------------
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

-- =============================================================================
-- Indexes
-- =============================================================================

-- transactions: most queries filter by business + date range
CREATE INDEX IF NOT EXISTS idx_transactions_business_date
    ON transactions (business_id, date);

-- invoices: client risk scorer and scenario planner filter by business/client/status
CREATE INDEX IF NOT EXISTS idx_invoices_business_client_status
    ON invoices (business_id, client_id, status);

-- cash_flow_forecasts: dashboard/forecast API queries by business + forecast window
CREATE INDEX IF NOT EXISTS idx_forecasts_business_date
    ON cash_flow_forecasts (business_id, forecast_date);
