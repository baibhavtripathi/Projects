"""
Camunda Batch Monitor — CLI entry point.

Usage:
    python -m camunda_monitor
    python -m camunda_monitor --config "path/to/config.env"
"""

import argparse
import logging
from logging.handlers import TimedRotatingFileHandler
import os
import sys

from camunda_monitor.config import load_config
from camunda_monitor.api import check_process
from camunda_monitor.notifier import send_status, send_error


def setup_telemetry():
    """Configure logging to write to both console and a daily rotating log file."""
    log_dir = os.path.join(os.getcwd(), "logs")
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, "camunda-monitor.log")
    
    # Rotates log file every day at midnight, keeping 30 days history
    file_handler = TimedRotatingFileHandler(log_file, when="midnight", interval=1, backupCount=30, encoding='utf-8')
    file_handler.suffix = "%Y-%m-%d.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            file_handler,
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(
        prog="camunda_monitor",
        description="Monitor Camunda 7 batch processes and send Google Chat alerts.",
    )
    parser.add_argument(
        "--config",
        default=os.path.join(os.path.dirname(__file__), "..", "..", "config", ".env.example"),
        help="Path to the .env configuration file (default: config/.env.example)",
    )
    return parser.parse_args()


def main() -> None:
    """Main application flow."""
    logger = setup_telemetry()
    logger.info("=== Starting Camunda Batch Monitor ===")
    
    args = parse_args()
    logger.info(f"Loading configuration from: {args.config}")
    
    config = load_config(args.config)
    webhook_url = config["GOOGLE_CHAT_WEBHOOK"]
    process_keys = config.get("PROCESS_KEYS", [])

    try:
        process_status = "Batch Completed!"
        is_active = False
        has_incident = False
        incident_details = []
        process_variables = {}
        instance_count = 0

        # Check each process in priority order; stop at the first active one
        for process_key in process_keys:
            logger.info(f"Telemetry API Call: Checking for active instances of '{process_key}'...")
            result = check_process(config, process_key)

            if result["is_active"]:
                process_status = process_key
                is_active = True
                instance_count = result["instance_count"]
                has_incident = result["has_incident"]
                incident_details = result["incidents"]
                process_variables = result.get("variables", {})

                if has_incident:
                    logger.warning(f"Telemetry Result: {len(incident_details)} incident(s) found on {process_key}")
                else:
                    logger.info(f"Telemetry Result: {instance_count} active instance(s) running, no incidents")
                    
                if process_variables:
                    logger.info(f"Telemetry Variables: Extracted mapped process variables {list(process_variables.keys())}")

                break  # Found an active process, no need to check the next
            else:
                logger.info(f"Telemetry Result: No active instances for {process_key}")

        # Send the notification
        logger.info("Telemetry Webhook Call: Dispatching payload to Google Chat...")
        send_status(
            webhook_url=webhook_url,
            process_status=process_status,
            is_active=is_active,
            has_incident=has_incident,
            incident_details=incident_details,
            instance_count=instance_count,
            process_variables=process_variables,
            all_processes=process_keys
        )
        logger.info("=== Execution Completed Successfully ===")

    except Exception as e:
        logger.error(f"Execution failed: {e}", exc_info=True)
        try:
            send_error(webhook_url, str(e))
        except Exception:
            pass
        sys.exit(1)


if __name__ == "__main__":
    main()
