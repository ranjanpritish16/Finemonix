from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from backend.database import get_db
from backend.models import Client

router = APIRouter(prefix="/clients", tags=["Clients"])

@router.get("/{business_id}/risk")
async def get_clients_risk(
    business_id: int, 
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Client).where(Client.business_id == business_id)
    result = await db.execute(stmt)
    clients = result.scalars().all()
    
    if not clients:
        return []
        
    response = []
    for client in clients:
        rev_share = float(client.total_revenue_share) if client.total_revenue_share else 0.0
        avg_delay = client.avg_payment_delay_days if client.avg_payment_delay_days else 0
        
        # Reliability score: 100 - (avg_delay_days * 2), clamped 0-100
        rel_score = max(0, min(100, 100 - (avg_delay * 2)))
        
        # Concentration thresholds: <15%=low, 15-30%=medium, 30-50%=high, >50%=critical
        if rev_share < 15.0:
            conc_risk = "low"
        elif rev_share < 30.0:
            conc_risk = "medium"
        elif rev_share < 50.0:
            conc_risk = "high"
        else:
            conc_risk = "critical"
            
        response.append({
            "client_id": client.id,
            "name": client.canonical_name,
            "revenue_share_pct": rev_share,
            "avg_payment_delay_days": avg_delay,
            "reliability_score": rel_score,
            "concentration_risk_level": conc_risk
        })
        
    return response
