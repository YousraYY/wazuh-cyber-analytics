import requests
from requests.auth import HTTPBasicAuth

OPENSEARCH_URL = "http://localhost:9200"
INDEX_NAME = "wazuh-ml-alerts"
AUTH = HTTPBasicAuth("admin", "SecretPassword")


def send_ml_logs_to_wazuh(df):
    """
    Send ML-enriched logs back to OpenSearch (Wazuh)
    """
    for _, row in df.iterrows():
        doc = {
            "@timestamp": row["@timestamp"].isoformat()
            if "@timestamp" in row and hasattr(row["@timestamp"], "isoformat")
            else None,

            "source_ip": row.get("source_ip") or row.get("src_ip"),
            "dest_ip": row.get("dest_ip"),
            "protocol": row.get("protocol"),
            "action": row.get("action"),

            "ml": {
                "model": row.get("ml_model", "IsolationForest"),
                "anomaly_score": float(row.get("anomaly_score", 0)),
                "prediction": row.get("prediction", "unknown"),
                "risk_score": int(row.get("risk_score", 0))
            },

            "original_index": row.get("_index", "unknown")
        }

        requests.post(
            f"{OPENSEARCH_URL}/{INDEX_NAME}/_doc",
            json=doc,
            auth=AUTH,
            timeout=5
        )
