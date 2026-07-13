# Wazuh Cyber Analytics

A SIEM analytics platform combining **Wazuh**, **Machine Learning**, and a **Streamlit** dashboard to detect and triage security threats — built to reduce the manual analysis burden and false-positive noise that traditional rule-based SIEMs generate.

> Academic project — ENSAM Casablanca, Filiere Cybersecurity and Cloud computing (CSCC-2, 2025-2026)

---

## Why this project

Manual log analysis doesn't scale against modern attack volume:

- +300% log growth year-over-year, millions of events/day to analyze
- 60% of SOC analyst time lost to false positives; average detection time of 6–8 hours
- Traditional SIEMs run 40–50% false-positive rates and miss zero-day threats
- Average cost of a breach: $4.45M (Statista/IBM), often with poor ROI on unoptimized tooling

This project combines Wazuh's log centralization with a trained ML classifier to score and flag events by risk, cutting through static rule noise.

---

## Architecture

A modular, three-layer design:

1. **Collection & Storage** — Wazuh centralizes ingestion, normalization, and storage (Elasticsearch) of security logs from servers and endpoints.
2. **Analytics & ML** — Streamlit serves as the interactive layer (Data Explorer, Visualizations, ML Predictions, Performance). Python modules handle the Wazuh connection, field extraction, cleaning, and a full ML pipeline (Random Forest) that generates risk scores and labels.
3. **Automation & Actions** — ML predictions are re-injected into Wazuh to enrich the original logs. Rule-based thresholds trigger alerts by risk score, and an automation script runs the simulate → analyze → notify loop continuously.

**Key design choices:** independent, swappable components (modularity), and a closed loop — Wazuh → ML → Wazuh — so every prediction enriches the system it came from rather than living in a separate silo.

### Wazuh deployment (Docker Compose)

| Service | Role | Port |
|---|---|---|
| `wazuh.manager` | Log collection & analysis | 1514/tcp, 514/udp, 55000 |
| `wazuh.indexer` | Storage & search (Elasticsearch-based) | 9200 |
| `wazuh.dashboard` | Alert visualization | 443 (HTTPS) |

### Two data sources feed the pipeline

1. **Real cybersecurity dataset** — reduced from ~6M raw logs to 10,000 representative samples (CSV). Used to test ingestion, explore data, and train/validate the ML model. Fields include `timestamp`, `source_ip`/`dest_ip`, `protocol`, `action`, `threat_label`, `log_type`, `bytes_transferred`, `user_agent`, `request_path`.
2. **Log Simulator** (`inject_logs1.py`) — generates synthetic traffic: ~85% normal activity (SSH, HTTP, DNS, DB connections) and ~15% suspicious/attack logs (scans, brute force, SQL injection, exfiltration). Simulates a full 6-phase attack chain: reconnaissance → vulnerability scanning → SSH brute force → lateral movement → data exfiltration → persistence. Supports both historical injection (Elasticsearch Bulk API) and real-time injection (writes to `/var/ossec/logs/imported_logs.json`).

---

## Machine Learning pipeline

**Objective:** classify security logs as normal (benign) or suspicious/malicious, complementing Wazuh's static rules with a predictive layer.

**Preprocessing:** numeric normalization (StandardScaler), categorical encoding, 75/25 train/test split, class imbalance handling (`class_weight=balanced`).

**Feature engineering:** temporal features (hour, day of week), network features (internal vs. external IP, source == destination flag), high-cardinality attributes (raw IPs, user-agent strings, paths) dropped in favor of engineered signals.

**Models compared:**

| Metric | Logistic Regression | Random Forest |
|---|---|---|
| Precision | 0.87 | **0.93** |
| Recall | 0.87 | 0.67 |
| F1-Score | 0.87 | 0.75 |

**Random Forest was selected**, primarily for its higher precision (0.93) — when it flags something as malicious, it's right more often, which matters for reducing alert fatigue in a SOC context. Worth being upfront about the tradeoff: its recall (0.67) is notably lower than Logistic Regression's (0.87), meaning it misses more true attacks in exchange for fewer false alarms. Depending on the SOC's risk appetite, that's a real design decision, not a free win — a security context that prioritizes "catch everything, review later" might reasonably prefer the higher-recall model instead.

The trained model is saved as `.joblib` and loaded by the Streamlit ML Predictions page for inference.

---

## Streamlit dashboard

Multi-page app, structured for maintainability:

```
streamlit_app/
├── app.py                    # entry point
├── config.py                 # app configuration
├── requirements.txt
├── .env                       # Wazuh connection secrets (not committed)
├── pages/
│   ├── 1_📊_Data_Explorer.py
│   ├── 2_📈_Visualisation.py
│   ├── 3_🤖_ML_Predictions.py
│   └── 4_📋_Performance.py
└── utils/
    ├── wazuh_connector.py     # auth, log retrieval, caching, retry logic
    ├── field_extractor.py     # parses nested Wazuh JSON into flat fields
    ├── data_processing.py     # cleaning, encoding, normalization, feature engineering
    └── ml_model.py            # sklearn pipeline, GridSearchCV, joblib persistence
```

| Page | What it does |
|---|---|
| 📊 **Data Explorer** | Connects to Wazuh Indexer (or loads simulated/CSV data), shows total logs / unique IPs / event types / avg risk, interactive filterable table, export to CSV/JSON/Excel |
| 📈 **Visualizations** | Temporal analysis (events by hour/day, hourly distribution), top active agents, global stats (unique agents, period covered) |
| 🤖 **ML Predictions** | Loads `ml_model.joblib`, scores incoming logs 0–100, classifies normal/suspect/critical, surfaces top 20 highest-risk events with confidence, downloadable results |
| 📋 **Performance** | Global metrics (total events, detection rate, avg risk, critical event count), Normal vs. Attack breakdown, risk score distribution, critical events timeline, full performance report |

**Data flow:** Wazuh Indexer → `wazuh_connector` → `field_extractor` (flattens nested JSON) → `data_processing` (cleaning + feature engineering) → either displayed directly (Data Explorer / Visualizations) or scored by `ml_model` (ML Predictions), with predictions re-injected into Wazuh and compared against outcomes on the Performance page.

---

## Automation — Zero-Click SOC pipeline

Without automation, a SOC doesn't scale: manual analysis, static rules, high response time. This project runs a continuous, unattended loop instead:

1. **Generate logs** — realistic simulated activity (normal / suspicious / attack), auto-timestamped
2. **Inject into Wazuh** — via OpenSearch API, indexed in real time, compatible with existing Wazuh dashboards
3. **Retrieve intelligently** — timestamp-based, only new logs, no duplicate processing
4. **Analyze with ML** — pre-trained model scores each event and classifies it normal / suspect / critical
5. **Enrich & alert** — risk score and ML prediction get written back into Wazuh; risk-score thresholds trigger alerts automatically

No manual steps once running — designed as a starting point for a real SOC pipeline, not just a one-off demo.

---

## Problems encountered (and how they were solved)

Documenting these honestly because they were real integration issues, not just a smooth tutorial run:

| Problem | Cause | Fix |
|---|---|---|
| Couldn't connect to Wazuh API | Wrong URL (`wazuh.indexer` instead of a resolvable host) | Corrected to `https://localhost:9200` |
| `Cannot mix tz-aware with tz-naive values` | Wazuh timestamps inconsistently timezone-aware | Standardized with `.dt.tz_localize(None)` |
| Fields showing as `"unknown"` | Complex nested Wazuh structure wasn't being extracted | Added `enrich_wazuh_data()` to auto-fill from available context |
| `unhashable type: 'dict'` during cleaning | Wazuh columns containing nested dicts | Extract/flatten fields *before* running cleaning steps |
| ML model incompatible with live Wazuh data | Feature mismatch between training data and Wazuh's schema | Built a feature-preparation step to align incoming data with the model's expected input |

**Broader technical challenges:** timestamp synchronization across components, keeping log formats consistent between the simulator and real Wazuh output, communication between independently-developed modules, and Wazuh index management.

---

## Getting started

### 1. Deploy Wazuh (Docker, single-node)

Increase `max_map_count` on your host (Linux, requires root):
```bash
sysctl -w vm.max_map_count=262144
```

Generate certificates:
```bash
docker-compose -f generate-indexer-certs.yml run --rm generator
```

Start the environment:
```bash
docker-compose up -d
```

First startup takes about a minute while the Wazuh Indexer initializes indexes and patterns.

### 2. Set up the Streamlit dashboard

```bash
cd streamlit_app
pip install -r requirements.txt
cp .env.example .env   # fill in your Wazuh connection details
streamlit run app.py
```

### 3. (Optional) Train the ML models yourself

```bash
cd ml_pipeline
python train_compare.py   # compares Random Forest vs Logistic Regression
python train.py           # trains and saves the selected model
```

Trained model files are excluded from version control (see `ml_pipeline/.gitignore`) — run the training scripts locally to regenerate them.

### 4. (Optional) Generate synthetic traffic

```bash
cd data_generation
python inject_logs1.py
```

---

## Data

Sample datasets (5k / 10k alerts) are included in the repo for quick testing without a live Wazuh instance. The full raw alert export (~850MB) is excluded from version control due to size — regenerate a comparable dataset with the log simulator above.

---

## Future improvements

- Message queue (Kafka / RabbitMQ) for higher-throughput log processing
- Dynamic, adaptive alert thresholds instead of fixed risk cutoffs
- Multi-agent scalability for larger deployments
- Continuous/online model retraining as new labeled data accumulates

---

## Limitations

This is an academic project, not a production-hardened deployment. The ML model was trained primarily on a reduced sample (10k of ~6M original logs) plus simulated traffic — it hasn't been validated against a live, adversarial, real-world threat feed. The precision/recall tradeoff documented above (favoring precision over recall) is a deliberate choice worth re-evaluating depending on deployment context.

---

## Project structure

```
wazuh-cyber-analytics/
├── automation/          # pipeline orchestration (fetch → predict → push)
├── config/              # Wazuh docker deployment config
├── data_generation/     # synthetic log/attack simulation (inject_logs1.py)
├── ml_pipeline/         # model training, comparison, and inference
├── streamlit_app/       # dashboard (multi-page Streamlit app)
├── alerts_5k.csv        # sample dataset (5,000 alerts)
├── alerts_10k.csv       # sample dataset (10,000 alerts)
└── docker-compose.yml   # Wazuh stack definition
```

---

## Author

Built by [Yousra](https://github.com/YousraYY) — Cybersécurité & Cloud Computing student at ENSAM Casablanca.