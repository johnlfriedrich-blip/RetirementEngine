from backend.services import historical


def test_load_spx_ohlcv():
    df = historical.load_spx_ohlcv()
    assert not df.empty
    assert "sp500" in df.columns


def test_load_market_data():
    df = historical.load_market_data()
    assert {"sp500", "bonds", "cpi"}.issubset(df.columns)


def test_real_returns():
    df = historical.load_real_returns()
    assert {"real_sp500", "real_bonds"}.issubset(df.columns)
    assert df.isna().sum().sum() == 0
