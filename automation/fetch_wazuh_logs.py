import requests
import pandas as pd
from datetime import datetime
import json
import logging

def fetch_logs(config, last_timestamp):
    try:
        query = {
            "size": 1000,
            "sort": [{"@timestamp": "asc"}],
            "query": {
                "range": {
                    "@timestamp": {
                        "gt": last_timestamp
                    }
                }
            }
        }

        response = requests.post(
            f"{config['wazuh']['host']}/{config['wazuh']['source_index']}/_search",
            auth=(config["wazuh"]["username"], config["wazuh"]["password"]),
            headers={"Content-Type": "application/json"},
            json=query,
            verify=config["wazuh"]["verify_ssl"],
            timeout=15
        )

        response.raise_for_status()
        hits = response.json()["hits"]["hits"]

        if not hits:
            return pd.DataFrame(), last_timestamp

        records = []
        for h in hits:
            src = h["_source"]
            src["@timestamp"] = src["@timestamp"]
            records.append(src)

        df = pd.json_normalize(records)
        new_last_timestamp = df["@timestamp"].max()

        return df, new_last_timestamp

    except Exception as e:
        logging.exception("❌ Failed to fetch logs from Wazuh")
        return pd.DataFrame(), last_timestamp
