from fastapi import APIRouter

router = APIRouter(prefix="/loan", tags=["Loan"])


@router.get("/status")
async def loan_status():
    return {"status": "ok"}
