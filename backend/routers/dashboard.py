from fastapi import APIRouter

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/status")
async def dashboard_status():
    return {"status": "ok"}
