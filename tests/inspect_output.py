from pathlib import Path
import pandas as pd

file_path = Path.home() / "Downloads" / "fact_orders.csv"
df = pd.read_csv(file_path)

print(df[[
    "status", "created_at", "shipped_at", "delivered_at",
    "prep_time", "delivery_time", "is_slow"
]].head(10).to_string(index=False))