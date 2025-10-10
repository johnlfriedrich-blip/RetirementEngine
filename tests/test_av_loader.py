# tests/test_av_loader.py

from retirement_engine.av_loader import fetch_daily_prices

def test_fetch_vti_daily_prices():
    df = fetch_daily_prices("VTI")
    assert not df.empty, "DataFrame is empty — API may have failed or rate-limited"
    assert "1. open" in df.columns, "Expected '1. open' column not found"
    assert df.index.name == "date", "Expected index name 'date' not found"