import pandas as pd
import requests
from requests.auth import HTTPBasicAuth
import json
import urllib3

urllib3.disable_warnings()

OPENSEARCH_URL = "http://localhost:9200"
INDEX_NAME = "wazuh-alerts-csv"
AUTH = HTTPBasicAuth("admin", "SecretPassword")

df = pd.read_csv("alerts_5k.csv")

bulk_lines = []

for _, row in df.iterrows():
    bulk_lines.append(json.dumps({"index": {}}))
    bulk_lines.append(json.dumps(row.to_dict(), default=str))

payload = "\n".join(bulk_lines) + "\n"

response = requests.post(
    f"{OPENSEARCH_URL}/{INDEX_NAME}/_bulk",
    data=payload,
    headers={"Content-Type": "application/x-ndjson"},
    auth=AUTH,
    timeout=30
)

print("Status:", response.status_code)
print(response.text[:500])
