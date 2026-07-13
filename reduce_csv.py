import pandas as pd

INPUT = "alerts.csv"
OUTPUT = "alerts_5k.csv"

df = pd.read_csv(INPUT)

# Option A: random sample (recommended)
df_small = df.sample(n=5000, random_state=42)

# Option B: first rows (faster)
# df_small = df.head(5000)

df_small.to_csv(OUTPUT, index=False)

print(f"Saved {len(df_small)} rows to {OUTPUT}")
