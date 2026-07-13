import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime
import json
import numpy as np
import pandas as pd

OPENSEARCH_URL = "http://localhost:9200"
INDEX_NAME = "wazuh-ml-alerts"
AUTH = HTTPBasicAuth("admin", "SecretPassword")


def _json_safe(value):
    """Convert numpy / pandas types to JSON-safe"""
    if isinstance(value, (np.integer, np.int64)):
        return int(value)
    if isinstance(value, (np.floating, np.float64)):
        return float(value)
    if isinstance(value, (pd.Timestamp, datetime)):
        return value.isoformat()
    if pd.isna(value):
        return None
    return value


def send_ml_alerts_to_wazuh(df):
    headers = {"Content-Type": "application/json"}
    sent = 0
    failed = 0

    for _, row in df.iterrows():
        # -----------------------------
        # Build clean document
        # -----------------------------
        doc = {k: _json_safe(v) for k, v in row.to_dict().items()}

        # Ensure @timestamp
        if "@timestamp" not in doc or not doc["@timestamp"]:
            doc["@timestamp"] = datetime.utcnow().isoformat()

        # Attach ML namespace (BEST PRACTICE)
        doc["ml"] = {
            "prediction": doc.get("ml_prediction"),
            "risk_score": int(doc.get("risk_score", 0)),
            "confidence": float(doc.get("confidence", 0)),
            "model": "streamlit-ml-v1"
        }

        # -----------------------------
        # Send to OpenSearch
        # -----------------------------
        try:
            r = requests.post(
                f"{OPENSEARCH_URL}/{INDEX_NAME}/_doc",
                auth=AUTH,
                headers=headers,
                data=json.dumps(doc),
                timeout=5
            )

            if r.status_code in (200, 201):
                sent += 1
            else:
                failed += 1
                print("❌ OpenSearch error:", r.text)

        except Exception as e:
            failed += 1
            print("❌ Exception:", e)

    return sent, failed
