# backend/tasks/extraction_tasks.py

import asyncio
import logging
from celery import shared_task

logger = logging.getLogger(__name__)


async def _run_extraction(filing_id: int) -> dict:
    """
    Creates a fresh engine per call so the asyncpg pool is fully
    disposed before asyncio.run() closes the event loop.
    """
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from sqlalchemy import select
    from backend.config import get_settings
    from backend.models import Filing
    from backend.services.pdf_extractor import (
        extract_filing_text,
        generate_mock_filing_text,
    )

    s = get_settings()
    engine = create_async_engine(s.DATABASE_URL, pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    try:
        async with session_factory() as db:
            result = await db.execute(
                select(Filing).where(Filing.id == filing_id)
            )
            filing = result.scalar_one_or_none()
            if not filing:
                logger.error(f"Filing {filing_id} not found")
                return {"error": "not found"}

            if not filing.pdf_path:
                text = generate_mock_filing_text(
                    filing.filing_type or "General",
                    filing.subject or "",
                    filing.company_bse_code,
                )
                extractor = "mock"
                confidence = None
            else:
                text, extractor, confidence = extract_filing_text(filing.pdf_path)

            status = "processed"
            if extractor == "tesseract" and confidence is not None and confidence < 0.7:
                status = "low_confidence"

            filing.raw_text = text
            filing.extraction_status = status
            filing.extractor_used = extractor
            filing.ocr_confidence = confidence

            await db.commit()

            return {
                "filing_id": filing_id,
                "extractor": extractor,
                "confidence": confidence,
                "status": status,
                "text_length": len(text),
            }
    finally:
        await engine.dispose()


async def _get_pending_ids() -> list:
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from sqlalchemy import select
    from backend.config import get_settings
    from backend.models import Filing

    s = get_settings()
    engine = create_async_engine(s.DATABASE_URL, pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    try:
        async with session_factory() as db:
            result = await db.execute(
                select(Filing.id).where(Filing.extraction_status == "pending")
            )
            return [row[0] for row in result.fetchall()]
    finally:
        await engine.dispose()


@shared_task(name="tasks.process_filing_pdf", bind=True, max_retries=2)
def process_filing_pdf_task(self, filing_id: int):
    try:
        result = asyncio.run(_run_extraction(filing_id))
        logger.info(f"Extraction complete for filing {filing_id}: {result}")
        return result
    except Exception as exc:
        logger.error(f"Extraction failed for filing {filing_id}: {exc}")
        raise self.retry(exc=exc, countdown=30 * (2 ** self.request.retries))


@shared_task(name="tasks.process_all_pending_filings")
def process_all_pending_filings():
    pending_ids = asyncio.run(_get_pending_ids())
    for fid in pending_ids:
        process_filing_pdf_task.delay(fid)
    logger.info(f"Dispatched extraction for {len(pending_ids)} pending filings")
    return {"dispatched": len(pending_ids)}