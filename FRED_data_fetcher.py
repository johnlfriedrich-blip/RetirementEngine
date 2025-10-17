import pandas as pd
import pandas_datareader.data as web
from datetime import datetime

# Set date range (from FRED's earliest coverage)
start = datetime(1927, 1, 1)
end = datetime.today()

# S&P 500 Index (FRED series: 'SP500')
sp500 = web.DataReader("SP500", "fred", start, end)

# US 10-Year Treasury Constant Maturity (FRED series: 'DGS10')
ust10y = web.DataReader("DGS10", "fred", start, end)

# Save to CSV
sp500.to_csv("sp500_daily_fred.csv")
ust10y.to_csv("us10y_daily_fred.csv")

print("Data downloaded. S&P500 rows:", len(sp500))
print("US 10Y Treasury rows:", len(ust10y))
