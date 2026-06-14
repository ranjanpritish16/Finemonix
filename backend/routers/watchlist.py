# backend/routers/watchlist.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from backend.database import get_db
from backend.models import CompanyWatched, Business
from backend.schemas.watchlist import (
    AddCompanyRequest,
    CompanyWatchedOut,
    AnomalyTimelineResponse,
    RunAnomalyRequest,
)
from backend.services.anomaly_service import (
    run_isolation_forest,
    upsert_anomaly_scores,
    get_anomaly_timeline,
)
from backend.services.demo_fixture import get_demo_data

router = APIRouter(prefix="/watchlist", tags=["Watchlist"])


@router.post("/add", response_model=CompanyWatchedOut, status_code=201)
async def add_company(
    payload: AddCompanyRequest,
    db: AsyncSession = Depends(get_db),
):
    """Add a listed company to the business's watchlist."""
    # Verify business exists
    biz = await db.get(Business, payload.business_id)
    if not biz:
        raise HTTPException(status_code=404, detail="Business not found")

    # Prevent duplicates
    existing = await db.execute(
        select(CompanyWatched).where(
            CompanyWatched.business_id == payload.business_id,
            CompanyWatched.company_bse_code == payload.company_bse_code,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Company already in watchlist")

    entry = CompanyWatched(
        business_id=payload.business_id,
        company_name=payload.company_name,
        company_bse_code=payload.company_bse_code,
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry


@router.get("/companies", response_model=list[CompanyWatchedOut])
async def list_companies(
    business_id: int,
    db: AsyncSession = Depends(get_db),
):
    """List all companies on the watchlist for a business."""
    result = await db.execute(
        select(CompanyWatched).where(CompanyWatched.business_id == business_id)
    )
    return result.scalars().all()


@router.delete("/remove/{entry_id}", status_code=204)
async def remove_company(
    entry_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Remove a company from the watchlist."""
    entry = await db.get(CompanyWatched, entry_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Watchlist entry not found")
    await db.delete(entry)
    await db.commit()


@router.post("/anomaly/run", response_model=AnomalyTimelineResponse)
async def run_anomaly_detection(
    payload: RunAnomalyRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Run Isolation Forest on a company's quarterly financial ratios.
    Pass use_demo_data=true to use built-in DHFL/YESBANK/INFY fixture data.
    Pass use_demo_data=false and supply quarterly_data for real data.
    """
    if payload.use_demo_data:
        data = get_demo_data(payload.company_bse_code)
        if not data:
            raise HTTPException(
                status_code=404,
                detail=f"No demo data for '{payload.company_bse_code}'. "
                       f"Available: DHFL, YESBANK, INFY"
            )
    else:
        if not payload.quarterly_data or len(payload.quarterly_data) < 4:
            raise HTTPException(
                status_code=422,
                detail="Provide at least 4 quarters in quarterly_data"
            )
        data = payload.quarterly_data

    try:
        scored = run_isolation_forest(data)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    await upsert_anomaly_scores(db, payload.company_bse_code, scored)

    return AnomalyTimelineResponse(
        company_bse_code=payload.company_bse_code,
        quarters_analysed=len(scored),
        scores=scored,
    )


@router.get("/anomaly/timeline/{bse_code}", response_model=AnomalyTimelineResponse)
async def get_anomaly_timeline_endpoint(
    bse_code: str,
    db: AsyncSession = Depends(get_db),
):
    """Fetch previously computed anomaly scores for a company."""
    scores = await get_anomaly_timeline(db, bse_code)
    if not scores:
        raise HTTPException(
            status_code=404,
            detail=f"No anomaly data for '{bse_code}'. Run /anomaly/run first."
        )
    return AnomalyTimelineResponse(
        company_bse_code=bse_code,
        quarters_analysed=len(scores),
        scores=scores,
    )