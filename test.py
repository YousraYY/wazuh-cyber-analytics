import requests
from requests.auth import HTTPBasicAuth
import urllib3

urllib3.disable_warnings()

r = requests.get(
    "http://localhost:9200/_cluster/health",
    auth=HTTPBasicAuth("admin", "SecretPassword"),
    verify=False,   # 🔥 THIS IS THE KEY
    timeout=10
)

print("STATUS:", r.status_code)
print(r.json())
