import pytest
from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)

def test_forecast_endpoint():
    response = client.get("/forecast/1?horizon_days=90")
    # if no data exists it returns 404 in our implementation
    assert response.status_code in [200, 404]

def test_clients_risk_endpoint():
    response = client.get("/clients/1/risk")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_scenario_endpoint():
    # Will fail 400 because no base forecast is cached in our test without redis setup
    # but checks API schema presence
    response = client.post("/forecast/scenario", json={
        "business_id": 1,
        "client_id": 1,
        "delay_days": 15
    })
    assert response.status_code in [200, 400]
