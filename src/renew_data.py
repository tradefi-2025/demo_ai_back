import os
import datetime
import pandas as pd
import refinitiv.data as rd
import matplotlib.pyplot as plt

# ==== CONFIG ====
FOLDER_PATH = "/home/kian/NO_NAME/DEMO/Histories/indices"
os.makedirs(FOLDER_PATH, exist_ok=True)

# Indices to fetch (example: S&P 500, NASDAQ Composite, Dow Jones)
INDICES = ["SPY.N","QQQ.O", "DIA.N"]
# ==== LOGIN ====
rd.open_session(config_name="/home/kian/NO_NAME/DEMO/src/refinitiv-data.config.json")

# ==== TIME RANGE ====
end_time = datetime.datetime.utcnow()  # Yesterday
start_time = end_time - datetime.timedelta(days=365)  # 1 year of data

def fetch_daily_index(index_name):
    """Fetch daily closing prices for a given index."""
    try:
        data = rd.get_history(
            index_name,
            start=start_time,
            end=end_time,
            interval="1min",
            fields=["TRDPRC_1"]
        )
        if data.empty:
            print(f"❌ No data returned for {index_name}")
            return
        
        # Save full data
        file_path = os.path.join(FOLDER_PATH, f"{index_name.replace('#','')}_daily.csv")
        data.to_csv(file_path, index=True)
        print(f"✅ Saved daily data for {index_name}: {len(data)} rows")

        

    except Exception as e:
        print(f"❌ Error fetching {index_name}: {e}")

# ==== RUN ====
for index in INDICES:
    fetch_daily_index(index)

rd.close_session()
