# backend/routers/graph.py

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from backend.services.neo4j_client import get_neo4j_client
from backend.services.qdrant_client import get_qdrant_client

router = APIRouter(prefix="/graph", tags=["Graph"])


# ------------------------------------------------------------------
# Static routes FIRST (before dynamic /{company_code} routes)
# ------------------------------------------------------------------

@router.get("/status")
async def graph_status():
    neo4j_ok = False
    qdrant_ok = False
    qdrant_info = {}

    try:
        neo4j_ok = get_neo4j_client().verify_connectivity()
    except Exception:
        pass

    try:
        qdrant_info = get_qdrant_client().collection_info()
        qdrant_ok = True
    except Exception:
        pass


    return {
        "neo4j": {"connected": neo4j_ok},
        "qdrant": {"connected": qdrant_ok, **qdrant_info},
    }


@router.get("/qdrant/info")
async def qdrant_info():
    """Qdrant collection stats."""
    try:
        return get_qdrant_client().collection_info()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scrape/seed/historical")
async def trigger_historical_seed():
    """One-time: seed 2 years of historical filings for DHFL, YESBANK, INFY."""
    from backend.tasks.scraper_tasks import seed_historical_filings
    task = seed_historical_filings.delay()
    return {"task_id": task.id, "status": "queued"}


@router.post("/scrape/{company_code}")
async def trigger_scrape(
    company_code: str,
    lookback_days: int = 30,
):
    """Manually trigger a BSE filing scrape for a company."""
    from backend.tasks.scraper_tasks import scrape_company_filings_task
    task = scrape_company_filings_task.delay(
        company_code.upper(), lookback_days
    )
    return {
        "task_id": task.id,
        "company_bse_code": company_code.upper(),
        "lookback_days": lookback_days,
        "status": "queued",
    }

@router.post("/extract/all-pending")
async def extract_all_pending():
    """Trigger text extraction for all pending filings."""
    from backend.tasks.extraction_tasks import process_all_pending_filings
    task = process_all_pending_filings.delay()
    return {"task_id": task.id, "status": "queued"}


@router.post("/extract/{filing_id}")
async def extract_single_filing(filing_id: int):
    """Trigger text extraction for a single filing."""
    from backend.tasks.extraction_tasks import process_filing_pdf_task
    task = process_filing_pdf_task.delay(filing_id)
    return {"task_id": task.id, "filing_id": filing_id, "status": "queued"}

@router.post("/nlp/run-all")
async def run_all_nlp():
    """Trigger NLP pipeline for all processed filings without NLP results."""
    from backend.tasks.nlp_tasks import run_all_pending_nlp
    task = run_all_pending_nlp.delay()
    return {"task_id": task.id, "status": "queued"}


@router.post("/nlp/run/{filing_id}")
async def run_nlp_single(filing_id: int):
    """Trigger NLP pipeline for a single filing."""
    from backend.tasks.nlp_tasks import run_nlp_pipeline_task
    task = run_nlp_pipeline_task.delay(filing_id)
    return {"task_id": task.id, "filing_id": filing_id, "status": "queued"}



# ------------------------------------------------------------------
# Dynamic /{company_code} routes AFTER static routes
# ------------------------------------------------------------------

@router.get("/{company_code}/directors")
async def get_directors(company_code: str):
    """List all directors for a company."""
    try:
        directors = get_neo4j_client().get_company_directors(company_code.upper())
        return {"company_bse_code": company_code.upper(), "directors": directors}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{company_code}/pledge-history")
async def get_pledge_history(company_code: str):
    """Promoter pledge percentage history for a company."""
    try:
        history = get_neo4j_client().get_pledge_history(company_code.upper())
        return {"company_bse_code": company_code.upper(), "pledge_history": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{company_code}/related-parties")
async def get_related_parties(company_code: str):
    """Related party transactions for a company."""
    try:
        parties = get_neo4j_client().get_related_parties(company_code.upper())
        return {"company_bse_code": company_code.upper(), "related_parties": parties}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{company_code}/neighbors")
async def get_neighbors(
    company_code: str,
    depth: int = Query(default=2, ge=1, le=3),
    entity_types: Optional[str] = Query(
        default=None,
        description="Comma-separated: Company,Person,AuditorFirm"
    ),
):
    """
    Return nodes + edges for a D3 force graph up to `depth` hops.
    Used by the frontend knowledge graph explorer.
    """
    types = entity_types.split(",") if entity_types else None
    try:
        graph = get_neo4j_client().get_neighbors(
            bse_code=company_code.upper(),
            depth=depth,
            entity_types=types,
        )
        return {"company_bse_code": company_code.upper(), **graph}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/nlp/results/{bse_code}")
async def get_nlp_results(bse_code: str):
    """Get NLP results for all filings of a company."""
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    from sqlalchemy import select
    from backend.config import get_settings
    from backend.models import Filing, FilingNlpResult

    s = get_settings()
    engine = create_async_engine(s.DATABASE_URL, pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    try:
        async with session_factory() as db:
            result = await db.execute(
                select(Filing, FilingNlpResult)
                .join(FilingNlpResult, Filing.id == FilingNlpResult.filing_id)
                .where(Filing.company_bse_code == bse_code.upper())
                .order_by(Filing.filing_date)
            )
            rows = result.fetchall()

        return {
            "company_bse_code": bse_code.upper(),
            "filings_analysed": len(rows),
            "results": [
                {
                    "filing_id": f.id,
                    "filing_date": str(f.filing_date),
                    "filing_type": f.filing_type,
                    "subject": f.subject,
                    "entities_found": len(n.entities or []),
                    "extracted_ratios": n.extracted_ratios,
                    "audit_opinions": n.audit_opinions,
                    "regulatory_terms": n.regulatory_terms,
                    "promoter_actions": n.promoter_actions,
                    "nlp_status": n.nlp_status,
                }
                for f, n in rows
            ],
        }
    finally:
        await engine.dispose()