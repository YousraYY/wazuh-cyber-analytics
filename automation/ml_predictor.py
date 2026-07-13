import pandas as pd
import joblib
import logging

def apply_ml(df, config):
    try:
        model = joblib.load(config["ml"]["model_path"])

        df["timestamp"] = pd.to_datetime(df["@timestamp"], errors="coerce")

        df["hour"] = df["timestamp"].dt.hour.fillna(0).astype(int)
        df["day"] = df["timestamp"].dt.dayofweek.fillna(0).astype(int)

        df["same_ip"] = (df["source_ip"] == df["dest_ip"]).astype(int)
        df["internal_src"] = df["source_ip"].astype(str).str.startswith("192.168").astype(int)
        df["internal_dst"] = df["dest_ip"].astype(str).str.startswith("192.168").astype(int)

        df_model = df[[
            "bytes_transferred",
            "hour",
            "day",
            "same_ip",
            "internal_src",
            "internal_dst",
            "protocol",
            "action",
            "log_type"
        ]].copy()

        proba = model.predict_proba(df_model)[:, 1]
        df["risk_score"] = (proba * 100).round(2)

        df["prediction"] = df["risk_score"].apply(
            lambda x: "normal"
            if x < config["ml"]["risk_thresholds"]["normal"]
            else "suspicious"
            if x < config["ml"]["risk_thresholds"]["suspicious"]
            else "critical"
        )

        df["model"] = "RandomForest"
        return df

    except Exception:
        logging.exception("❌ ML inference failed")
        return pd.DataFrame()
