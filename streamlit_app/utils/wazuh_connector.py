# utils/wazuh_connector.py
import json
from datetime import datetime

import requests
import pandas as pd
from requests.auth import HTTPBasicAuth
import urllib3
import streamlit as st

from config import (
    WAZUH_INDEXER_URL,
    WAZUH_INDEXER_USER,
    WAZUH_INDEXER_PASSWORD,
    WAZUH_ALERTS_INDEX,
    WAZUH_INDEXER_VERIFY_SSL
)

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class WazuhConnector:
    def __init__(self):
        self.indexer_url = WAZUH_INDEXER_URL.rstrip("/")
        self.auth = HTTPBasicAuth(
            WAZUH_INDEXER_USER,
            WAZUH_INDEXER_PASSWORD
        )

    def test_indexer(self):
        """Check OpenSearch availability"""
        try:
            r = requests.get(
                f"{self.indexer_url}/_cluster/health",
                auth=self.auth,
                verify=WAZUH_INDEXER_VERIFY_SSL,
                timeout=10
            )
            return r.status_code == 200
        except:
            return False

    def fetch_alerts(self, size=1000):
        try:
            r = requests.post(
                f"{self.indexer_url}/{WAZUH_ALERTS_INDEX}/_search",
                auth=self.auth,
                verify=WAZUH_INDEXER_VERIFY_SSL,
                json={
                    "size": size,
                    "query": {"match_all": {}},
                    "sort": [{"timestamp": {"order": "desc"}}]
                },
                timeout=30
            )
            r.raise_for_status()
            hits = r.json()["hits"]["hits"]
            return [h["_source"] for h in hits], None
        except Exception as e:
            return [], str(e)

    def logs_to_dataframe(self, logs):
        if not logs:
            return pd.DataFrame()

        df = pd.DataFrame(logs)

        if "timestamp" in df.columns:
            df["@timestamp"] = pd.to_datetime(
                df["timestamp"], errors="coerce", utc=True
            )

        defaults = {
            "type": "unknown",
            "src_ip": "0.0.0.0",
            "dest_ip": "0.0.0.0",
            "agent": "unknown",
            "risk_score": 0
        }

        for col, val in defaults.items():
            if col not in df.columns:
                df[col] = val

        return df
    
    # ==========================================================
    # SEND ML ALERTS TO OPENSEARCH
    # ==========================================================
    def send_ml_alerts(self, df, index_name="wazuh-ml-alerts"):
        """
        Send ML-scored alerts to OpenSearch (Wazuh Indexer)
        """
        if df.empty:
            return False, "DataFrame vide"

        headers = {"Content-Type": "application/json"}
        bulk_payload = ""

        for _, row in df.iterrows():
            doc = {
                "@timestamp": row.get("@timestamp"),
                "src_ip": row.get("src_ip"),
                "dest_ip": row.get("dest_ip"),
                "agent": row.get("agent"),
                "ml_prediction": row.get("ml_prediction"),
                "confidence": float(row.get("confidence", 0)),
                "risk_score": int(row.get("risk_score", 0)),
                "model": "streamlit-ml",
                "ingested_at": datetime.utcnow().isoformat()
            }

            bulk_payload += json.dumps(
                {"index": {"_index": index_name}}
            ) + "\n"
            bulk_payload += json.dumps(doc) + "\n"

        try:
            r = requests.post(
                f"{self.indexer_url}/_bulk",
                data=bulk_payload,
                headers=headers,
                auth=self.indexer_auth,
                verify=False,
                timeout=30
            )
            r.raise_for_status()
            return True, f"{len(df)} alertes ML envoyées"
        except Exception as e:
            return False, str(e)



@st.cache_resource
def get_wazuh_connector():
    return WazuhConnector()
