from fastapi import APIRouter

router = APIRouter(prefix="/data", tags=["Data"])


@router.get("/status")
async def data_status():
    return {"status": "ok"}
