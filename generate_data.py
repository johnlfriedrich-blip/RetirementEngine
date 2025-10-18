import csv

with open("data/market.csv", "w", newline="") as csvfile:
    fieldnames = ["sp500", "bonds"]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

    writer.writeheader()
    for i in range(300):
        writer.writerow({"sp500": 100 + i, "bonds": 100 + i})
