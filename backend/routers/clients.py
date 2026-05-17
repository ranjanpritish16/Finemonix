from fastapi import APIRouter

router = APIRouter(prefix="/clients", tags=["Clients"])


@router.get("/status")
async def clients_status():
    return {"status": "ok"}
