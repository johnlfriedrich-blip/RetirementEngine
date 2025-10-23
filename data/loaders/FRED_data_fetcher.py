import pandas_datareader.data as web
from datetime import datetime
import os

# Set date range (from FRED's earliest coverage)
start = datetime(1927, 1, 1)
end = datetime.today()

# Define the raw data directory
raw_data_dir = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "src", "data", "raw"
)
os.makedirs(raw_data_dir, exist_ok=True)

# S&P 500 Index (FRED series: 'SP500')
sp500 = web.DataReader("SP500", "fred", start, end)

# US 10-Year Treasury Constant Maturity (FRED series: 'DGS10')
ust10y = web.DataReader("DGS10", "fred", start, end)

# Consumer Price Index for All Urban Consumers: All Items (FRED series: 'CPIAUCSL')
cpi = web.DataReader("CPIAUCSL", "fred", start, end)

# Save to CSV
sp500.to_csv(os.path.join(raw_data_dir, "sp500.csv"))
ust10y.to_csv(os.path.join(raw_data_dir, "us10y.csv"))
cpi.to_csv(os.path.join(raw_data_dir, "cpi_fred.csv"))

print("Data downloaded. S&P500 rows:", len(sp500))
print("US 10Y Treasury rows:", len(ust10y))
print("CPI rows:", len(cpi))
