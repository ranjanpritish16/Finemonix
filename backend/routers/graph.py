from fastapi import APIRouter

router = APIRouter(prefix="/graph", tags=["Graph"])


@router.get("/status")
async def graph_status():
    return {"status": "ok"}
