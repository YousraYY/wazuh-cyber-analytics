# config.py
import os

# ==========================================================
# WAZUH INDEXER (OpenSearch)
# ==========================================================
# Streamlit runs on the HOST machine (not inside Docker),
# so we MUST use localhost + exposed port.
#
# IMPORTANT:
# - Wazuh Indexer uses HTTP by default on 9200
# - Using https here WILL cause: SSL WRONG_VERSION_NUMBER

WAZUH_INDEXER_URL = os.getenv(
    "WAZUH_INDEXER_URL",
    "http://localhost:9200"
)

WAZUH_INDEXER_USER = os.getenv(
    "WAZUH_INDEXER_USER",
    "admin"
)

WAZUH_INDEXER_PASSWORD = os.getenv(
    "WAZUH_INDEXER_PASSWORD",
    "SecretPassword"
)

# Indexer does NOT use SSL in your setup
WAZUH_INDEXER_VERIFY_SSL = False


# ==========================================================
# WAZUH API (Manager)
# ==========================================================
# The Wazuh API DOES use HTTPS with self-signed certs

WAZUH_API_URL = os.getenv(
    "WAZUH_API_URL",
    "https://localhost:55000"
)

WAZUH_API_USER = os.getenv(
    "WAZUH_API_USER",
    "wazuh-wui"
)

WAZUH_API_PASSWORD = os.getenv(
    "WAZUH_API_PASSWORD",
    "wazuh-wui"
)

# Self-signed certificates → MUST be False
WAZUH_API_VERIFY_SSL = False


# ==========================================================
# WAZUH ALERT INDICES
# ==========================================================
# We intentionally use a wildcard to support:
#   - wazuh-alerts-4.x-YYYY.MM.DD
#   - wazuh-alerts-csv
#   - any future custom alert index

WAZUH_ALERTS_INDEX = "wazuh-alerts*"


# ==========================================================
# STREAMLIT APP CONFIG
# ==========================================================
APP_TITLE = "🛡️ Wazuh ML Cybersecurity Dashboard"
APP_ICON = "🛡️"
LAYOUT = "wide"


# ==========================================================
# PATHS & CACHE
# ==========================================================
DATA_DIR = "data"
CACHE_EXPIRY = 300  # seconds (5 minutes)
