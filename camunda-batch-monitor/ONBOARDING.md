# Camunda Batch Monitor: Onboarding & Architecture Guide

This guide is designed to help you understand the architecture, design decisions, and core technologies behind the **Camunda Batch Monitor**. 

This application serves as a great introduction to modern Python development best practices, API integrations, and secure application distribution.

---

## 1. Project Background and Purpose

### The Problem
Previously, monitoring our Camunda batch processes (`BatchProcess` and `LmdBatchProcess`) was done using a **Selenium-based automation script**. That script launched a visible Chrome browser, physically "clicked" through the web UI, took screenshots, and used an internal Microsoft Outlook client (`win32com`) to send emails. 

**Drawbacks of the old approach:**
- **Fragile:** Any minor change to the Camunda Web UI would break the script.
- **Slow & Invasive:** Booting a browser is resource-intensive and disruptive.
- **Incompatible:** Cannot easily be run headless on an isolated server without browser environments or Outlook installed.
- **Security:** Credentials and file paths were hardcoded directly in the Python files.

### The Solution (This Application)
We refactored the project into an **API-first, container-ready Python application**.
## The Configuration (`.env`) File

The core behaviour of the app relies on environment variables. We separate concerns so secrets aren't inside the code.

Crucial variables included inside your `.env` file:
*   URL and Authentication credentials.
*   Webhook address payload destination.
*   `PROCESS_KEYS`: Which processes are checked (in order).
*   `TRACKED_VARIABLES`: Extract specific instance variables (`jobId`, `CCAT`, etc.) directly into notifications.


---
- **Camunda 7 REST API:** We query the engine directly via HTTP. It's lightning fast and immune to UI changes.
- **Google Chat Webhooks:** Alerts go directly to team chat channels, eliminating the need for email servers or local Outlook clients.
- **Config-Driven:** Uses `.env` files to isolate secrets and define logic (e.g. `PROCESS_KEYS` and `TRACKED_VARIABLES`).
- **Telemetry & Logging:** Stores rotating daily log files inside `/logs/` to provide a complete audit trail without cluttering the main directory.
- **Packaged Executables:** Built using PyInstaller so it can run anywhere without installing Python.

---

## 2. Project Architecture

The application is structured as a standard modular Python package:

```text
camunda-batch-monitor/
├── pyproject.toml              # Makes the application pip-installable
├── requirements.txt            # Python dependencies (requests, python-dotenv, pytest)
├── camunda-monitor.spec        # PyInstaller build instructions
├── config/
│   └── .env.example            # Boilerplate config to show what parameters are needed
├── src/camunda_monitor/        # Main application package
│   ├── api.py                  # Handles all Camunda HTTP REST requests
│   ├── config.py               # Validates and loads the .env configuration
│   ├── notifier.py             # Formats and sends Google Chat Card v2 payloads
│   └── __main__.py             # Entry point (links config → api → notifier)
└── tests/                      # Unit testing suite (pytest)
```

### The Execution Flow
1. **Load Config:** User runs `camunda-monitor.exe --config "path.env"`. `config.py` loads and validates the file.
2. **Query API:** `api.py` checks for active instances of `BatchProcess`.
3. **Fallback:** If none are found, it queries `LmdBatchProcess`.
4. **Check Incidents:** If an active instance is found, it queries the `/incident` REST endpoint for errors.
5. **Notify:** `notifier.py` builds an interactive Google Chat card summarizing the health and pushes it via the webhook.

---

## 3. Core Technologies & Technical Concepts

### A. Environment Variables and Secret Management
**Concept:** Hardcoding credentials (`user="admin"`) is a security risk. Best practice is loading configurations from the environment.
**Implementation:** We use the `python-dotenv` library. Specifically, instead of injecting variables into the global `os.environ` space, we use `dotenv_values()` to tightly scope the configurations to a Python dictionary mapping within `config.py`.
**Resource:** [Python Dotenv documentation](https://pypi.org/project/python-dotenv/)

### B. REST API Integration (`requests`)
**Concept:** REpresentational State Transfer (REST) is the standard for interacting with modern web servers.
**Implementation:** `api.py` uses the standard Python `requests` library. We use **HTTP Basic Auth** (`auth=(user, password)`) which is standard for Camunda 7 self-managed deployments. We also gracefully handle self-signed certificates common in internal enterprise servers by appending `verify=False`. 
**Resources:**
- [Python Requests Library Guide](https://realpython.com/python-requests/)
- [Camunda 7 REST API Reference](https://docs.camunda.org/manual/7.20/reference/rest/)

### C. Webhooks and ChatOps
**Concept:** A Webhook is a way for an app to provide other applications with real-time information by sending an HTTP POST request to a provided URL.
**Implementation:** `notifier.py` sends `POST` requests to a Google Chat Webhook URL. Authentication is uniquely baked directly into the URL itself. We formulate the payload using Google Chat's "Card v2" format to create rich, widget-based messages.
**Resources:**
- [What is a Webhook?](https://sendgrid.com/blog/whats-webhook/)
- [Google Chat API: Message Formats & Cards](https://developers.google.com/workspace/chat/format-messages)

### D. Unit Testing and Mocking (`pytest`)
**Concept:** Writing automated tests ensures that when you alter the logic next year, you don't break existing functionality. 
**Implementation:** We use `pytest`. Because our application calls external servers (Camunda and Google Chat), we use **Mocking** (via Python's `unittest.mock.patch`). This allows us to "fake" the HTTP responses so the tests run in milliseconds without requiring actual network access.
**Resources:**
- [Getting Started with Pytest](https://docs.pytest.org/en/7.4.x/getting-started.html)
- [Understanding Python Mocking](https://realpython.com/python-mock-library/)

### E. Distribution via Application Freezing (`PyInstaller`)
**Concept:** Standard Python scripts require the target server to install Python and configure dependency packages (`pip install`). "Freezing" bundles the Python interpreter and all application code into one single `executable`.
**Implementation:** We use `PyInstaller` with a customized `camunda-monitor.spec` file. The output `dist/camunda-monitor.exe` can be securely transferred to any Windows server and executed via Task Scheduler effortlessly.
**Resource:** [PyInstaller Documentation](https://pyinstaller.org/en/stable/operating-mode.html)

---

## 4. Maintenance Guide for Newcomers

As you onboard to manage this infrastructure, here are practical workflows to follow:

### Developing and Testing Locally
1. Ensure your Python virtual environment has the dev requirements:
   ```bash
   pip install -e .
   pip install -r requirements.txt
   ```
2. Any time you alter logic in `src/`, verify you haven't broken anything by running the test suite:
   ```bash
   python -m pytest tests/ -v
   ```

### Releasing an Update
Whenever modifying business requirements, you must rebuild the executable:
```bash
python -m PyInstaller camunda-monitor.spec --distpath dist --workpath build --noconfirm
```
Take the newly generated `dist/camunda-monitor.exe` file, pair it with the target environment's `.env` configuration file, and deploy it to the server.

### Extending the Application
Future enhancements might include:
- Adding email fallbacks if the Chat Webhook fails.
- Upgrading to OAuth tokens if transitioning from Camunda 7 to Camunda 8 (using the Operate API).
- Tracking variable payloads attached to specific failed incidents.
