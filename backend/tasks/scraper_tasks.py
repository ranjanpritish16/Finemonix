# backend/tasks/scraper_tasks.py

import asyncio
import logging
from backend.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)

WATCHED_BSE_CODES = ["DHFL", "YESBANK", "INFY"]


async def _run_scrape(bse_code: str, lookback_days: int) -> dict:
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from backend.config import get_settings
    from backend.services.bse_scraper import scrape_company_filings

    s = get_settings()
    engine = create_async_engine(s.DATABASE_URL, pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    try:
        async with session_factory() as db:
            return await scrape_company_filings(db, bse_code, lookback_days)
    finally:
        await engine.dispose()


@celery_app.task(name="tasks.scrape_company_filings", bind=True, max_retries=3)
def scrape_company_filings_task(self, bse_code: str, lookback_days: int = 30):
    from backend.services.bse_scraper import DEMO_COMPANIES
    if bse_code.upper() in DEMO_COMPANIES:
        lookback_days = 365 * 3

    try:
        result = asyncio.run(_run_scrape(bse_code, lookback_days))
        logger.info(f"Scrape complete for {bse_code}: {result}")
        return result
    except Exception as exc:
        logger.error(f"Scrape failed for {bse_code}: {exc}")
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@celery_app.task(name="tasks.scrape_all_watched")
def scrape_all_watched():
    for bse_code in WATCHED_BSE_CODES:
        scrape_company_filings_task.delay(bse_code, lookback_days=30)
    return {"dispatched": len(WATCHED_BSE_CODES)}


@celery_app.task(name="tasks.seed_historical_filings")
def seed_historical_filings():
    historical = [
        ("DHFL",    2 * 365),
        ("YESBANK", 2 * 365),
        ("INFY",    2 * 365),
    ]
    results = {}
    for bse_code, lookback_days in historical:
        result = scrape_company_filings_task.apply(
            args=[bse_code, lookback_days]
        ).get(timeout=300)
        results[bse_code] = result
    return results