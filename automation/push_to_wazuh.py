import requests
import logging

def push_logs(df, config):
    try:
        for _, row in df.iterrows():
            response = requests.post(
                f"{config['wazuh']['host']}/{config['wazuh']['target_index']}/_doc",
                auth=(config["wazuh"]["username"], config["wazuh"]["password"]),
                headers={"Content-Type": "application/json"},
                json=row.dropna().to_dict(),
                verify=config["wazuh"]["verify_ssl"],
                timeout=10
            )
            response.raise_for_status()

    except Exception:
        logging.exception("❌ Failed to push enriched logs to Wazuh")
