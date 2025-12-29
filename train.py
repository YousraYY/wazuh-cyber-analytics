import pandas as pd
import numpy as np
import joblib

from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.ensemble import RandomForestClassifier

# =========================
# CONFIG
# =========================
CSV_PATH = "logs.csv"   # put CSV in same folder
SAMPLE_SIZE = 100_000   # SAFE SAMPLE

print("🚀 Training started")

# =========================
# LOAD DATA (SAMPLED)
# =========================
df = pd.read_csv(CSV_PATH, nrows=SAMPLE_SIZE)
print(f"✅ Loaded {len(df)} rows")

# =========================
# FEATURE ENGINEERING
# =========================
df["timestamp"] = pd.to_datetime(df["timestamp"])

df["hour"] = df["timestamp"].dt.hour
df["day"] = df["timestamp"].dt.dayofweek

# IP features (VERY IMPORTANT)
df["same_ip"] = (df["source_ip"] == df["dest_ip"]).astype(int)
df["internal_src"] = df["source_ip"].str.startswith("192.168").astype(int)
df["internal_dst"] = df["dest_ip"].str.startswith("192.168").astype(int)

# Encode target
df["label"] = (df["threat_label"] != "benign").astype(int)

# Drop unused / high-cardinality columns
df = df.drop(columns=[
    "timestamp",
    "threat_label",
    "source_ip",
    "dest_ip",
    "user_agent",     # HIGH cardinality
    "request_path"    # HIGH cardinality
])

print("📊 Label distribution:")
print(df["label"].value_counts())

X = df.drop(columns=["label"])
y = df["label"]

# =========================
# FEATURE TYPES
# =========================
num_features = [
    "bytes_transferred",
    "hour",
    "day",
    "same_ip",
    "internal_src",
    "internal_dst"
]

cat_features = [
    "protocol",
    "action",
    "log_type"
]

# =========================
# PREPROCESSING
# =========================
preprocessor = ColumnTransformer(
    transformers=[
        ("num", StandardScaler(), num_features),
        ("cat", OneHotEncoder(handle_unknown="ignore"), cat_features)
    ]
)

# =========================
# MODEL
# =========================
model = RandomForestClassifier(
    n_estimators=100,
    max_depth=20,
    n_jobs=-1,
    random_state=42
)

pipeline = Pipeline([
    ("preprocess", preprocessor),
    ("model", model)
])

# =========================
# TRAIN / TEST SPLIT
# =========================
X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=0.25,
    random_state=42,
    stratify=y
)

# =========================
# TRAIN
# =========================
pipeline.fit(X_train, y_train)

# =========================
# EVALUATION
# =========================
y_pred = pipeline.predict(X_test)

print("\n📈 Classification Report:")
print(classification_report(y_test, y_pred))

print("🧩 Confusion Matrix:")
print(confusion_matrix(y_test, y_pred))

# =========================
# SAVE MODEL
# =========================
joblib.dump(pipeline, "ml_model.joblib")

with open("metrics.txt", "w") as f:
    f.write(classification_report(y_test, y_pred))

print("💾 Model saved as ml_model.joblib")
print("🏁 Training finished")
