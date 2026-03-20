# Camunda Batch Monitor

A lightweight Python application that monitors Camunda processes on a Camunda 7 platform via its REST API, detects active instances and incidents, and sends formatted status notifications to **Google Chat**.

## Features

- **Processes to monitor** — List processes in your `.env` file using key `PROCESS_KEYS`
- **REST API-based monitoring** — No browser/Selenium required; queries Camunda 7 `/engine-rest/` endpoints directly
- **Incident detection** — Checks for active incidents on running process instances and includes details in alerts
- **Google Chat notifications** — Sends rich Card v2 messages to a Google Chat Space via webhook
- **Configuration via `.env`** — All credentials and URLs loaded from an external config file using `dotenv_values`

## Project Structure

```
camunda-batch-monitor/
├── README.md
├── .gitignore
├── requirements.txt
├── config/
│   └── .env.example          # Config template (no secrets)
├── src/
│   └── camunda_monitor/
│       ├── __init__.py
│       ├── __main__.py        # CLI entry point
│       ├── config.py          # Config loader & validation
│       ├── api.py             # Camunda 7 REST API client
│       └── notifier.py        # Google Chat webhook sender
└── tests/
    └── __init__.py
```

## Prerequisites

- Python 3.8+
- Network access to your Camunda 7 engine (`/engine-rest/`)
- A Google Chat Space webhook URL

## Setup

1. **Clone / copy this project**

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

   >💡 **Note on Dependencies**<br>
   > `requirements.txt` uses minimum versions (`>=`) not pinned versions (`==`).
   > A compromised upstream update could be pulled in unintentionally.
   > Use `pip-compile` to freeze exact versions for production.

3. **Configure your environment:**

   Copy the example config and fill in your values:
   ```bash
   cp config/.env.example config/.env
   ```

   Or point to an existing `.env` file at runtime (see Usage below).

   Required keys:
   | Key | Description |
   |-----|-------------|
   | `CAMUNDA_URL` | Base URL of your Camunda instance (e.g. `https://host:8443/camunda`) |
   | `CAMUNDA_USERNAME` | REST API username |
   | `CAMUNDA_PASSWORD` | REST API password |
   | `GOOGLE_CHAT_WEBHOOK` | Google Chat Space webhook URL |
   | `PROCESS_KEYS` | Comma-separated list of process definition keys to monitor (e.g., `BatchProcess,LmdBatchProcess`) |
   | `TRACKED_VARIABLES` | Comma-separated list of process variables to extract and include in notifications (e.g., `processKey,CCAT,jobId`) |

## Usage

```bash
# Using the default config path (config/.env in this project)
python -m camunda_monitor

# Using a custom config file
python -m camunda_monitor --config "path/to/your.env"
```

## 🛠 Features

- **Multi-Process Support:** Dynamically scans processes defined in `PROCESS_KEYS`.
- **Variable Tracking:** Automatically extracts variables defined in `TRACKED_VARIABLES` and pushes them to Google Chat.
- **Automated Logging:** Telemetry is written to the `logs/` directory, automatically generating a new log file every day (midnight rotation).

## ⛷️ [Onboarding](https://baibhavtripathi.github.io/Projects/camunda-batch-monitor/ONBOARDING.html)


### How It Works

1. Loads configuration from the specified `.env` file
2. Queries `BatchProcess` for active instances via the Camunda 7 REST API
3. If no active instances, falls back to checking `LmdBatchProcess`
4. Checks for incidents on any active process instance found
5. Sends a formatted Google Chat card with the result:
   - 📊 **Running** — process name, instance count, timestamp
   - 🚨 **Incident** — error type and message details
   - ✅ **Completed** — both batch processes have finished
   - ❌ **Script Error** — failure details if the monitor itself errors

## 📜 License & Disclaimer

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

### 📌 Open Source Attribution
If you  use or share this software, please give proper credit to the original developer **[@baibhavtripathi](https://github.com/baibhavtripathi)**. 

### ⚠️ Liability Waiver
**THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND.** 
By using this software, you acknowledge that the authors or copyright holders shall **not be liable** for any claims, damages (including direct, indirect, incidental, or consequential damages), or other liabilities arising from your use, deployment, or modification of this software. You are solely responsible for compliance with any organizational security policies and operational limits when integrating with Camunda 7 REST APIs or Google Chat Webhooks.
