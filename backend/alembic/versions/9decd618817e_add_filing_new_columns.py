"""add_filing_new_columns
Revision ID: 9decd618817e
Revises: 7c2724988446
Create Date: 2026-06-17
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '9decd618817e'
down_revision: Union[str, Sequence[str], None] = '7c2724988446'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.add_column('filings', sa.Column('bse_news_id', sa.String(50), nullable=True, unique=True))
    op.add_column('filings', sa.Column('subject', sa.Text(), nullable=True))
    op.add_column('filings', sa.Column('pdf_path', sa.Text(), nullable=True))
    op.add_column('filings', sa.Column('ocr_confidence', sa.Numeric(4, 3), nullable=True))
    op.add_column('filings', sa.Column('dedup_hash', sa.String(64), nullable=True))
    op.create_unique_constraint('uq_filings_dedup_hash', 'filings', ['dedup_hash'])
    op.create_unique_constraint('uq_filings_bse_news_id', 'filings', ['bse_news_id'])
    op.create_index('ix_filings_company_bse_code', 'filings', ['company_bse_code'])

def downgrade() -> None:
    op.drop_index('ix_filings_company_bse_code', table_name='filings')
    op.drop_constraint('uq_filings_bse_news_id', 'filings', type_='unique')
    op.drop_constraint('uq_filings_dedup_hash', 'filings', type_='unique')
    op.drop_column('filings', 'dedup_hash')
    op.drop_column('filings', 'ocr_confidence')
    op.drop_column('filings', 'pdf_path')
    op.drop_column('filings', 'subject')
    op.drop_column('filings', 'bse_news_id')
