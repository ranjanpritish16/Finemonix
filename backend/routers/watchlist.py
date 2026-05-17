from fastapi import APIRouter

router = APIRouter(prefix="/watchlist", tags=["Watchlist"])


@router.get("/status")
async def watchlist_status():
    return {"status": "ok"}
