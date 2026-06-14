# backend/schemas/watchlist.py

from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class AddCompanyRequest(BaseModel):
    business_id: int
    company_name: str
    company_bse_code: str


class CompanyWatchedOut(BaseModel):
    id: int
    company_name: str
    company_bse_code: str

    class Config:
        from_attributes = True


class AnomalyScoreOut(BaseModel):
    quarter: str
    score_financial: float
    severity: str
    contributing_features: Dict[str, Any]


class AnomalyTimelineResponse(BaseModel):
    company_bse_code: str
    quarters_analysed: int
    scores: List[AnomalyScoreOut]


class RunAnomalyRequest(BaseModel):
    company_bse_code: str
    use_demo_data: bool = True   # False = expects real quarterly_data payload
    quarterly_data: Optional[List[Dict[str, Any]]] = None