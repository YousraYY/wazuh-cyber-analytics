import pandas as pd
import joblib

# =========================
# CONFIG
# =========================
MODEL_PATH = "ml_model.joblib"
INPUT_CSV = "new_logs.csv"       # logs to predict
OUTPUT_CSV = "predictions.csv"

print("🚀 Prediction started")

# =========================
# LOAD MODEL
# =========================
model = joblib.load(MODEL_PATH)
print("✅ Model loaded")

# =========================
# LOAD DATA
# =========================
df = pd.read_csv(INPUT_CSV)
print(f"📥 Loaded {len(df)} rows")

# =========================
# FEATURE ENGINEERING (MUST MATCH TRAINING)
# =========================
df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

df["hour"] = df["timestamp"].dt.hour.fillna(0).astype(int)
df["day"] = df["timestamp"].dt.dayofweek.fillna(0).astype(int)

df["same_ip"] = (df["source_ip"] == df["dest_ip"]).astype(int)
df["internal_src"] = df["source_ip"].astype(str).str.startswith("192.168").astype(int)
df["internal_dst"] = df["dest_ip"].astype(str).str.startswith("192.168").astype(int)

# Drop columns NOT used by model
df_model = df.drop(columns=[
    "timestamp",
    "threat_label",
    "source_ip",
    "dest_ip",
    "user_agent",
    "request_path"
], errors="ignore")

# =========================
# PREDICTION
# =========================
proba = model.predict_proba(df_model)[:, 1]

df["risk_score"] = (proba * 100).round(2)

df["prediction"] = df["risk_score"].apply(
    lambda x: "normal" if x < 30 else "suspicious" if x < 70 else "critical"
)

# =========================
# SAVE OUTPUT
# =========================
df.to_csv(OUTPUT_CSV, index=False)

print(f"💾 Predictions saved to {OUTPUT_CSV}")
print("🏁 Prediction finished")