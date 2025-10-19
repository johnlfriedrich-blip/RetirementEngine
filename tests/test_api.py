from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


def test_list_assets():
    response = client.get("/assets")
    assert response.status_code == 200
    assets = response.json()
    assert isinstance(assets, list)
    assert "us_equities" in assets
    assert "intl_equities" in assets
    assert "fixed_income" in assets


def test_run_simulation_success():
    portfolio = {
        "assets": {"us_equities": 0.6, "intl_equities": 0.3, "fixed_income": 0.1}
    }
    response = client.post("/simulate", json=portfolio)
    assert response.status_code == 200
    results = response.json()
    assert "success_rate" in results
    assert "median_final_balance" in results
    assert isinstance(results["success_rate"], float)
    assert isinstance(results["median_final_balance"], float)


def test_run_simulation_empty_portfolio():
    portfolio = {"assets": {}}
    response = client.post("/simulate", json=portfolio)
    assert response.status_code == 400
    error = response.json()
    assert error == {"detail": "Portfolio must not be empty."}


def test_run_simulation_invalid_weights():
    portfolio = {
        "assets": {"us_equities": 0.6, "intl_equities": 0.3, "fixed_income": 0.2}
    }
    response = client.post("/simulate", json=portfolio)
    assert response.status_code == 400
    error = response.json()
    assert error == {"detail": "Portfolio weights must sum to 1.0."}


def test_run_simulation_invalid_asset():
    portfolio = {
        "assets": {"us_equities": 0.6, "intl_equities": 0.3, "invalid_asset": 0.1}
    }
    response = client.post("/simulate", json=portfolio)
    assert response.status_code == 400
    error = response.json()
    assert error == {"detail": "Invalid asset class: invalid_asset"}
