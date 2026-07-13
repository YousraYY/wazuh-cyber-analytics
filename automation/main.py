from pathlib import Path
import time
import yaml
import json
import logging

# =========================
# PATHS (FIRST, ALWAYS)
# =========================
BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "config.yaml"
STATE_FILE = BASE_DIR / "state.json"
LOG_FILE = BASE_DIR / "automation.log"

# =========================
# PACKAGE IMPORTS
# =========================
from .fetch_wazuh_logs import fetch_logs
from .ml_predictor import apply_ml
from .push_to_wazuh import push_logs

# =========================
# LOAD CONFIG
# =========================
with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    config = yaml.safe_load(f)

# =========================
# LOGGING
# =========================
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logging.info("🚀 Automation started")

# =========================
# LOAD STATE (SAFE)
# =========================
last_timestamp = "now-10m"

if STATE_FILE.exists():
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if content:
                state = json.loads(content)
                last_timestamp = state.get("last_timestamp", last_timestamp)
    except Exception as e:
        logging.warning(f"⚠️ Invalid state.json, resetting state: {e}")

# =========================
# MAIN LOOP
# =========================
while True:
    logging.info("🔄 New automation cycle")

    df_logs, new_ts = fetch_logs(config, last_timestamp)

    if df_logs.empty:
        logging.info("ℹ️ No new logs")
    else:
        logging.info(f"📥 {len(df_logs)} new logs fetched")

        df_pred = apply_ml(df_logs, config)

        if not df_pred.empty:
            push_logs(df_pred, config)
            logging.info("📤 Enriched logs pushed to Wazuh")

    # =========================
    # SAVE STATE (SAFE)
    # =========================
    last_timestamp = new_ts
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump({"last_timestamp": last_timestamp}, f)

    time.sleep(config["schedule"]["interval_minutes"] * 60)
