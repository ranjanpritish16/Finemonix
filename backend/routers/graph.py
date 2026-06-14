# backend/routers/graph.py

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from backend.services.neo4j_client import get_neo4j_client
from backend.services.qdrant_client import get_qdrant_client

router = APIRouter(prefix="/graph", tags=["Graph"])


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


@router.get("/qdrant/info")
async def qdrant_info():
    """Qdrant collection stats."""
    try:
        return get_qdrant_client().collection_info()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))