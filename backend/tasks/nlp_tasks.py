# backend/tasks/nlp_tasks.py

import asyncio
import logging
from datetime import datetime, timezone
from celery import shared_task

logger = logging.getLogger(__name__)


async def _run_nlp(filing_id: int) -> dict:
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from sqlalchemy import select
    from backend.config import get_settings
    from backend.models import Filing, FilingNlpResult
    from backend.services.nlp_service import run_nlp_pipeline

    s = get_settings()
    engine = create_async_engine(s.DATABASE_URL, pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    try:
        async with session_factory() as db:
            # Fetch filing
            result = await db.execute(
                select(Filing).where(Filing.id == filing_id)
            )
            filing = result.scalar_one_or_none()
            if not filing:
                return {"error": f"Filing {filing_id} not found"}

            if not filing.raw_text:
                return {"error": f"Filing {filing_id} has no raw_text"}

            # Run NLP
            nlp_result = run_nlp_pipeline(filing.raw_text)

            # Upsert FilingNlpResult
            existing = await db.execute(
                select(FilingNlpResult).where(
                    FilingNlpResult.filing_id == filing_id
                )
            )
            nlp_row = existing.scalar_one_or_none()

            if nlp_row is None:
                nlp_row = FilingNlpResult(filing_id=filing_id)
                db.add(nlp_row)

            nlp_row.entities = nlp_result["entities"]
            nlp_row.extracted_ratios = nlp_result["extracted_ratios"]
            nlp_row.audit_opinions = nlp_result["audit_opinions"]
            nlp_row.regulatory_terms = nlp_result["regulatory_terms"]
            nlp_row.promoter_actions = nlp_result["promoter_actions"]
            nlp_row.nlp_status = nlp_result["nlp_status"]
            nlp_row.spacy_model = nlp_result["spacy_model"]
            nlp_row.processed_at = datetime.now(timezone.utc)

            await db.commit()

            return {
                "filing_id": filing_id,
                "entities_found": len(nlp_result["entities"]),
                "ratios_extracted": sum(
                    1 for v in nlp_result["extracted_ratios"].values()
                    if v is not None
                ),
                "audit_opinions": len(nlp_result["audit_opinions"]),
                "regulatory_terms": len(nlp_result["regulatory_terms"]),
                "promoter_actions": len(nlp_result["promoter_actions"]),
                "status": nlp_result["nlp_status"],
            }
    finally:
        await engine.dispose()


async def _get_nlp_pending_ids() -> list:
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from sqlalchemy import select
    from backend.config import get_settings
    from backend.models import Filing, FilingNlpResult

    s = get_settings()
    engine = create_async_engine(s.DATABASE_URL, pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    try:
        async with session_factory() as db:
            # Filings that are processed but have no NLP result yet
            processed = await db.execute(
                select(Filing.id).where(Filing.extraction_status == "processed")
            )
            processed_ids = {row[0] for row in processed.fetchall()}

            done = await db.execute(select(FilingNlpResult.filing_id))
            done_ids = {row[0] for row in done.fetchall()}

            return list(processed_ids - done_ids)
    finally:
        await engine.dispose()


@shared_task(name="tasks.run_nlp_pipeline", bind=True, max_retries=2)
def run_nlp_pipeline_task(self, filing_id: int):
    try:
        result = asyncio.run(_run_nlp(filing_id))
        logger.info(f"NLP complete for filing {filing_id}: {result}")
        return result
    except Exception as exc:
        logger.error(f"NLP failed for filing {filing_id}: {exc}")
        raise self.retry(exc=exc, countdown=30 * (2 ** self.request.retries))


@shared_task(name="tasks.run_all_pending_nlp")
def run_all_pending_nlp():
    pending_ids = asyncio.run(_get_nlp_pending_ids())
    for fid in pending_ids:
        run_nlp_pipeline_task.delay(fid)
    logger.info(f"Dispatched NLP for {len(pending_ids)} filings")
    return {"dispatched": len(pending_ids)}