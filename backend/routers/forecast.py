from fastapi import APIRouter

router = APIRouter(prefix="/forecast", tags=["Forecast"])


@router.get("/status")
async def forecast_status():
    return {"status": "ok"}
