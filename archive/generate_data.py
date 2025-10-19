import os
import csv

project_root = os.path.dirname(os.path.abspath(__file__))
market_csv_path = os.path.join(project_root, "..", "src", "data", "market.csv")
print(f"Attempting to write to: {market_csv_path}")

with open(market_csv_path, "w", newline="") as csvfile:
    fieldnames = ["sp500", "bonds"]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

    writer.writeheader()
    for i in range(300):
        writer.writerow({"sp500": 100 + i, "bonds": 100 + i})
