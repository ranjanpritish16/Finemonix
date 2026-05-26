from datetime import date, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import case, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.models import (
    AnomalyScore,
    Business,
    CashFlowForecast,
    Client,
    CompanyWatched,
    Transaction,
)

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/status")
async def dashboard_status():
    return {"status": "ok"}


@router.get("/{business_id}")
async def dashboard_summary(
    business_id: int,
    db: AsyncSession = Depends(get_db),
):
    today = date.today()
    month_start = today.replace(day=1)
    last_30_days = today - timedelta(days=30)

    business_result = await db.execute(
        select(Business).where(Business.id == business_id)
    )
    business = business_result.scalars().first()

    cash_result = await db.execute(
        select(
            func.coalesce(
                func.sum(
                    case(
                        (Transaction.direction == "in", Transaction.amount),
                        else_=-Transaction.amount,
                    )
                ),
                0,
            )
        ).where(Transaction.business_id == business_id)
    )
    current_balance = float(cash_result.scalar() or 0)

    revenue_expense_result = await db.execute(
        select(
            func.coalesce(
                func.sum(case((Transaction.direction == "in", Transaction.amount), else_=0)),
                0,
            ),
            func.coalesce(
                func.sum(case((Transaction.direction == "out", Transaction.amount), else_=0)),
                0,
            ),
        ).where(
            Transaction.business_id == business_id,
            Transaction.date >= month_start,
        )
    )
    month_revenue, month_expenses = revenue_expense_result.one()

    recent_transactions_result = await db.execute(
        select(Transaction)
        .where(Transaction.business_id == business_id)
        .order_by(desc(Transaction.date), desc(Transaction.id))
        .limit(5)
    )
    recent_transactions = recent_transactions_result.scalars().all()

    forecast_result = await db.execute(
        select(CashFlowForecast)
        .where(
            CashFlowForecast.business_id == business_id,
            CashFlowForecast.forecast_date >= today,
        )
        .order_by(CashFlowForecast.forecast_date)
    )
    forecasts = forecast_result.scalars().all()
    safety_threshold = float(business.safety_threshold_inr) if business else 50000.0
    danger_forecast = next(
        (
            forecast
            for forecast in forecasts
            if forecast.predicted_balance is not None
            and float(forecast.predicted_balance) < safety_threshold
        ),
        None,
    )

    client_risk_result = await db.execute(
        select(Client)
        .where(Client.business_id == business_id)
        .order_by(desc(Client.total_revenue_share), desc(Client.avg_payment_delay_days))
        .limit(3)
    )
    top_clients = client_risk_result.scalars().all()

    watchlist_count_result = await db.execute(
        select(func.count()).select_from(CompanyWatched).where(
            CompanyWatched.business_id == business_id
        )
    )
    total_watched = int(watchlist_count_result.scalar() or 0)

    latest_anomaly_result = await db.execute(
        select(AnomalyScore)
        .join(
            CompanyWatched,
            CompanyWatched.company_bse_code == AnomalyScore.company_bse_code,
        )
        .where(CompanyWatched.business_id == business_id)
        .order_by(desc(AnomalyScore.created_at))
        .limit(1)
    )
    latest_anomaly = latest_anomaly_result.scalars().first()

    high_alert_count_result = await db.execute(
        select(func.count())
        .select_from(AnomalyScore)
        .join(
            CompanyWatched,
            CompanyWatched.company_bse_code == AnomalyScore.company_bse_code,
        )
        .where(
            CompanyWatched.business_id == business_id,
            AnomalyScore.created_at >= last_30_days,
            AnomalyScore.severity.in_(["high", "critical", "alert", "danger"]),
        )
    )
    high_alert_count = int(high_alert_count_result.scalar() or 0)

    return {
        "business": {
            "id": business_id,
            "name": business.name if business else "Demo Business",
            "quality_score": business.quality_score if business else 0,
            "data_sources_connected": business.data_sources_connected if business else [],
        },
        "cash_summary": {
            "current_balance_inr": current_balance,
            "monthly_revenue_inr": float(month_revenue or 0),
            "monthly_expenses_inr": float(month_expenses or 0),
            "next_danger_zone_days": (
                (danger_forecast.forecast_date - today).days
                if danger_forecast
                else None
            ),
            "forecast_accuracy_pct": 0,
        },
        "loan_summary": {
            "best_approval_probability": 0,
            "best_lender_type": "Not scored yet",
            "top_blocking_factor": "Loan engine is not implemented yet",
        },
        "watchlist_summary": {
            "total_watched": total_watched,
            "high_alert_count": high_alert_count,
            "latest_alert": (
                {
                    "company_code": latest_anomaly.company_bse_code,
                    "alert_type": "Anomaly score",
                    "severity": latest_anomaly.severity,
                }
                if latest_anomaly
                else None
            ),
        },
        "client_risk_summary": {
            "high_concentration_clients": len(
                [
                    client
                    for client in top_clients
                    if float(client.total_revenue_share or 0) >= 30
                ]
            ),
            "top_clients": [
                {
                    "id": client.id,
                    "client_name": client.canonical_name,
                    "revenue_share_pct": float(client.total_revenue_share or 0),
                    "avg_payment_delay_days": client.avg_payment_delay_days or 0,
                    "bse_code": client.bse_code,
                }
                for client in top_clients
            ],
        },
        "recent_transactions": [
            {
                "id": transaction.id,
                "date": transaction.date.isoformat(),
                "counterparty": transaction.raw_description or "Unmapped counterparty",
                "direction": transaction.direction,
                "amount": float(transaction.amount),
                "source": transaction.source,
                "category": transaction.category or "General",
            }
            for transaction in recent_transactions
        ],
    }
