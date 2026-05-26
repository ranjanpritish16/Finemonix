"""initial schema

Revision ID: e290f1d5306d
Revises: 
Create Date: 2026-05-26 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'e290f1d5306d'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. businesses
    op.create_table(
        'businesses',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('gstin', sa.String(length=15), nullable=True),
        sa.Column('pan', sa.String(length=10), nullable=True),
        sa.Column('business_type', sa.String(length=50), nullable=True),
        sa.Column('onboarding_date', sa.Date(), nullable=False),
        sa.Column('data_sources_connected', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('quality_score', sa.Integer(), nullable=False),
        sa.Column('safety_threshold_inr', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('gstin')
    )
    # 2. users
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('business_id', sa.Integer(), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    # 3. clients
    op.create_table(
        'clients',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('business_id', sa.Integer(), nullable=False),
        sa.Column('canonical_name', sa.String(length=255), nullable=False),
        sa.Column('gstin', sa.String(length=15), nullable=True),
        sa.Column('is_listed_company', sa.Boolean(), nullable=False),
        sa.Column('bse_code', sa.String(length=20), nullable=True),
        sa.Column('total_revenue_share', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('avg_payment_delay_days', sa.Integer(), nullable=False),
        sa.Column('aliases', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    # 4. transactions
    op.create_table(
        'transactions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('business_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('direction', sa.String(length=3), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('counterparty_id', sa.Integer(), nullable=True),
        sa.Column('source', sa.String(length=10), nullable=False),
        sa.Column('raw_description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['counterparty_id'], ['clients.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    # 5. invoices
    op.create_table(
        'invoices',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('business_id', sa.Integer(), nullable=False),
        sa.Column('client_id', sa.Integer(), nullable=True),
        sa.Column('amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('issue_date', sa.Date(), nullable=False),
        sa.Column('due_date', sa.Date(), nullable=False),
        sa.Column('paid_date', sa.Date(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('days_overdue', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    # 6. cash_flow_forecasts
    op.create_table(
        'cash_flow_forecasts',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('business_id', sa.Integer(), nullable=False),
        sa.Column('generated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('forecast_date', sa.Date(), nullable=False),
        sa.Column('predicted_balance', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('p10_balance', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('p90_balance', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('model_version', sa.String(length=20), nullable=True),
        sa.Column('model_used', sa.String(length=10), nullable=True),
        sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    # 7. companies_watched
    op.create_table(
        'companies_watched',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('business_id', sa.Integer(), nullable=False),
        sa.Column('company_bse_code', sa.String(length=20), nullable=False),
        sa.Column('company_name', sa.String(length=255), nullable=False),
        sa.Column('added_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['business_id'], ['businesses.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('business_id', 'company_bse_code')
    )
    # 8. filings
    op.create_table(
        'filings',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('company_bse_code', sa.String(length=20), nullable=False),
        sa.Column('filing_type', sa.String(length=50), nullable=True),
        sa.Column('filing_date', sa.Date(), nullable=False),
        sa.Column('source_url', sa.Text(), nullable=True),
        sa.Column('raw_text', sa.Text(), nullable=True),
        sa.Column('extraction_status', sa.String(length=20), nullable=False),
        sa.Column('extractor_used', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    # 9. anomaly_scores
    op.create_table(
        'anomaly_scores',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('company_bse_code', sa.String(length=20), nullable=False),
        sa.Column('quarter', sa.String(length=10), nullable=False),
        sa.Column('score_financial', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('score_tone', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('score_graph', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('severity', sa.String(length=10), nullable=True),
        sa.Column('contributing_features', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    # 10. entities
    op.create_table(
        'entities',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('canonical_name', sa.String(length=255), nullable=False),
        sa.Column('entity_type', sa.String(length=20), nullable=False),
        sa.Column('cin', sa.String(length=21), nullable=True),
        sa.Column('pan', sa.String(length=10), nullable=True),
        sa.Column('aliases', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('canonical_name')
    )
    # 11. entity_aliases
    op.create_table(
        'entity_aliases',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('entity_id', sa.Integer(), nullable=False),
        sa.Column('alias', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['entity_id'], ['entities.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('alias')
    )
    # 12. filing_entities
    op.create_table(
        'filing_entities',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('filing_id', sa.Integer(), nullable=False),
        sa.Column('entity_id', sa.Integer(), nullable=False),
        sa.Column('mention_count', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['entity_id'], ['entities.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['filing_id'], ['filings.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('filing_id', 'entity_id')
    )

    # Indexes
    op.create_index('idx_transactions_business_date', 'transactions', ['business_id', 'date'], unique=False)
    op.create_index('idx_invoices_business_client_status', 'invoices', ['business_id', 'client_id', 'status'], unique=False)
    op.create_index('idx_forecasts_business_date', 'cash_flow_forecasts', ['business_id', 'forecast_date'], unique=False)
    op.create_index('idx_filings_bse_date', 'filings', ['company_bse_code', 'filing_date'], unique=False)
    op.create_index('idx_anomaly_scores_bse_quarter', 'anomaly_scores', ['company_bse_code', 'quarter'], unique=False)
    op.create_index('idx_entity_aliases_alias', 'entity_aliases', ['alias'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_entity_aliases_alias', table_name='entity_aliases')
    op.drop_index('idx_anomaly_scores_bse_quarter', table_name='anomaly_scores')
    op.drop_index('idx_filings_bse_date', table_name='filings')
    op.drop_index('idx_forecasts_business_date', table_name='cash_flow_forecasts')
    op.drop_index('idx_invoices_business_client_status', table_name='invoices')
    op.drop_index('idx_transactions_business_date', table_name='transactions')

    op.drop_table('filing_entities')
    op.drop_table('entity_aliases')
    op.drop_table('entities')
    op.drop_table('anomaly_scores')
    op.drop_table('filings')
    op.drop_table('companies_watched')
    op.drop_table('cash_flow_forecasts')
    op.drop_table('invoices')
    op.drop_table('transactions')
    op.drop_table('clients')
    op.drop_table('users')
    op.drop_table('businesses')
