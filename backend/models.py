from datetime import date, datetime
from typing import Any, Dict, List, Optional
from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.database import Base


class Business(Base):
    __tablename__ = "businesses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    gstin: Mapped[Optional[str]] = mapped_column(String(15), unique=True, nullable=True)
    pan: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    business_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    onboarding_date: Mapped[date] = mapped_column(Date, default=date.today)
    data_sources_connected: Mapped[List[str]] = mapped_column(JSONB, default=list)
    quality_score: Mapped[int] = mapped_column(Integer, default=0)
    safety_threshold_inr: Mapped[float] = mapped_column(Numeric(15, 2), default=50000.0)
    opening_balance: Mapped[float] = mapped_column(Numeric(15, 2), default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    users: Mapped[List["User"]] = relationship("User", back_populates="business", cascade="all, delete-orphan")
    clients: Mapped[List["Client"]] = relationship("Client", back_populates="business", cascade="all, delete-orphan")
    transactions: Mapped[List["Transaction"]] = relationship("Transaction", back_populates="business", cascade="all, delete-orphan")
    invoices: Mapped[List["Invoice"]] = relationship("Invoice", back_populates="business", cascade="all, delete-orphan")
    forecasts: Mapped[List["CashFlowForecast"]] = relationship("CashFlowForecast", back_populates="business", cascade="all, delete-orphan")
    watched_companies: Mapped[List["CompanyWatched"]] = relationship("CompanyWatched", back_populates="business", cascade="all, delete-orphan")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    business_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("businesses.id", ondelete="SET NULL"), nullable=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    business: Mapped[Optional[Business]] = relationship("Business", back_populates="users")


class Client(Base):
    __tablename__ = "clients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    business_id: Mapped[int] = mapped_column(Integer, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    canonical_name: Mapped[str] = mapped_column(String(255), nullable=False)
    gstin: Mapped[Optional[str]] = mapped_column(String(15), nullable=True)
    is_listed_company: Mapped[bool] = mapped_column(Boolean, default=False)
    bse_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    total_revenue_share: Mapped[float] = mapped_column(Numeric(5, 2), default=0.0)
    avg_payment_delay_days: Mapped[int] = mapped_column(Integer, default=0)
    aliases: Mapped[List[str]] = mapped_column(JSONB, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    business: Mapped[Business] = relationship("Business", back_populates="clients")
    transactions: Mapped[List["Transaction"]] = relationship("Transaction", back_populates="client")
    invoices: Mapped[List["Invoice"]] = relationship("Invoice", back_populates="client")


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    business_id: Mapped[int] = mapped_column(Integer, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    direction: Mapped[str] = mapped_column(String(3), nullable=False)  # 'in' or 'out'
    category: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    counterparty_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("clients.id", ondelete="SET NULL"), nullable=True)
    source: Mapped[str] = mapped_column(String(10), nullable=False)  # 'tally', 'gst', 'bank'
    raw_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    business: Mapped[Business] = relationship("Business", back_populates="transactions")
    client: Mapped[Optional[Client]] = relationship("Client", back_populates="transactions")


class Invoice(Base):
    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    business_id: Mapped[int] = mapped_column(Integer, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    client_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("clients.id", ondelete="SET NULL"), nullable=True)
    amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    issue_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    paid_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending")  # 'pending', 'paid', 'overdue', 'partial'
    days_overdue: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    source: Mapped[str] = mapped_column(String(10), default="manual")

    # Relationships
    business: Mapped[Business] = relationship("Business", back_populates="invoices")
    client: Mapped[Optional[Client]] = relationship("Client", back_populates="invoices")


class DataImportJob(Base):
    __tablename__ = "data_import_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    business_id: Mapped[int] = mapped_column(Integer, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    task_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    file_type: Mapped[str] = mapped_column(String(20), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="queued")
    percent: Mapped[int] = mapped_column(Integer, default=0)
    message: Mapped[str] = mapped_column(String(255), default="Queued in background")
    records_added: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    result: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class CashFlowForecast(Base):
    __tablename__ = "cash_flow_forecasts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    business_id: Mapped[int] = mapped_column(Integer, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    forecast_date: Mapped[date] = mapped_column(Date, nullable=False)
    predicted_balance: Mapped[Optional[float]] = mapped_column(Numeric(15, 2), nullable=True)
    p10_balance: Mapped[Optional[float]] = mapped_column(Numeric(15, 2), nullable=True)
    p90_balance: Mapped[Optional[float]] = mapped_column(Numeric(15, 2), nullable=True)
    model_version: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    model_used: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)

    # Relationships
    business: Mapped[Business] = relationship("Business", back_populates="forecasts")


class CompanyWatched(Base):
    __tablename__ = "companies_watched"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    business_id: Mapped[int] = mapped_column(Integer, ForeignKey("businesses.id", ondelete="CASCADE"), nullable=False)
    company_bse_code: Mapped[str] = mapped_column(String(20), nullable=False)
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    # Relationships
    business: Mapped[Business] = relationship("Business", back_populates="watched_companies")


class Filing(Base):
    __tablename__ = "filings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_bse_code: Mapped[str] = mapped_column(String(20), nullable=False)
    filing_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    filing_date: Mapped[date] = mapped_column(Date, nullable=False)
    source_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    raw_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    extraction_status: Mapped[str] = mapped_column(String(20), default="pending")  # 'pending', 'processed', 'failed'
    extractor_used: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class AnomalyScore(Base):
    __tablename__ = "anomaly_scores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_bse_code: Mapped[str] = mapped_column(String(20), nullable=False)
    quarter: Mapped[str] = mapped_column(String(10), nullable=False)
    score_financial: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    score_tone: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    score_graph: Mapped[Optional[float]] = mapped_column(Numeric(5, 2), nullable=True)
    severity: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)  # 'low', 'medium', 'high', 'critical'
    contributing_features: Mapped[Dict[str, Any]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class Entity(Base):
    __tablename__ = "entities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    canonical_name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    entity_type: Mapped[str] = mapped_column(String(20), nullable=False)  # 'company', 'person', 'auditor'
    cin: Mapped[Optional[str]] = mapped_column(String(21), nullable=True)
    gstin: Mapped[Optional[str]] = mapped_column(String(15), nullable=True)
    pan: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    aliases: Mapped[List[str]] = mapped_column(JSONB, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class EntityAlias(Base):
    __tablename__ = "entity_aliases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    entity_id: Mapped[int] = mapped_column(Integer, ForeignKey("entities.id", ondelete="CASCADE"), nullable=False)
    alias: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class FilingEntity(Base):
    __tablename__ = "filing_entities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    filing_id: Mapped[int] = mapped_column(Integer, ForeignKey("filings.id", ondelete="CASCADE"), nullable=False)
    entity_id: Mapped[int] = mapped_column(Integer, ForeignKey("entities.id", ondelete="CASCADE"), nullable=False)
    mention_count: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
