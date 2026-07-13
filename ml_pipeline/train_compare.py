import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.metrics import classification_report
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression

# =========================
# CONFIG
# =========================
CSV_PATH = "logs.csv"
SAMPLE_SIZE = 100_000

print("🚀 Model comparison training started")

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

df["same_ip"] = (df["source_ip"] == df["dest_ip"]).astype(int)
df["internal_src"] = df["source_ip"].astype(str).str.startswith("192.168").astype(int)
df["internal_dst"] = df["dest_ip"].astype(str).str.startswith("192.168").astype(int)

df["label"] = (df["threat_label"] != "benign").astype(int)

df = df.drop(columns=[
    "timestamp",
    "threat_label",
    "source_ip",
    "dest_ip",
    "user_agent",
    "request_path"
])

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

preprocessor = ColumnTransformer(
    transformers=[
        ("num", StandardScaler(), num_features),
        ("cat", OneHotEncoder(handle_unknown="ignore"), cat_features)
    ]
)

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
# MODELS TO COMPARE
# =========================
models = {
    "RandomForest": RandomForestClassifier(
        n_estimators=100,
        max_depth=20,
        class_weight="balanced",
        n_jobs=-1,
        random_state=42
    ),
    "LogisticRegression": LogisticRegression(
        max_iter=1000,
        class_weight="balanced"
    )
}

results = {}

# =========================
# TRAIN & EVALUATE
# =========================
for name, model in models.items():
    print(f"\n🔍 Training {name}")

    pipeline = Pipeline([
        ("preprocess", preprocessor),
        ("model", model)
    ])

    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)
    report = classification_report(y_test, y_pred, output_dict=True)

    results[name] = report

    # Save model
    joblib.dump(pipeline, f"ml_model_{name.lower()}.joblib")

    # Save metrics
    with open(f"metrics_{name.lower()}.txt", "w") as f:
        f.write(classification_report(y_test, y_pred))

    print(classification_report(y_test, y_pred))

# =========================
# COMPARISON SUMMARY
# =========================
rf_recall = results["RandomForest"]["1"]["recall"]
lr_recall = results["LogisticRegression"]["1"]["recall"]

with open("comparison_summary.txt", "w") as f:
    f.write("Model Comparison Summary\n")
    f.write("========================\n\n")
    f.write(f"Random Forest recall (malicious): {rf_recall:.3f}\n")
    f.write(f"Logistic Regression recall (malicious): {lr_recall:.3f}\n\n")

    if rf_recall > lr_recall:
        f.write("Random Forest selected (higher malicious recall)\n")
    else:
        f.write("Logistic Regression selected (higher malicious recall)\n")

print("\n🏁 Model comparison finished")