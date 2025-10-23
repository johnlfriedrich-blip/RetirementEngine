from backend.services.engine import run_backtest


def test_run_backtest():
    result = run_backtest()
    assert "final_balance" in result
    assert "success" in result
    assert isinstance(result["path"], list)
    assert len(result["path"]) > 0
