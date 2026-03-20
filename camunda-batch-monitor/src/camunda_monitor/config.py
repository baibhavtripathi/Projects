"""
Configuration loader — reads .env file using dotenv_values and validates required keys.
"""

import sys
from dotenv import dotenv_values


# Keys that must be present in the .env file for the app to function
REQUIRED_KEYS = [
    "CAMUNDA_URL",
    "CAMUNDA_USERNAME",
    "CAMUNDA_PASSWORD",
    "GOOGLE_CHAT_WEBHOOK",
    "PROCESS_KEYS",
]


def load_config(env_path: str) -> dict:
    """
    Load configuration from the given .env file path using dotenv_values.

    dotenv_values returns a plain dict without touching os.environ,
    keeping the config scoped and explicit.

    Args:
        env_path: Absolute or relative path to the .env file.

    Returns:
        dict with all configuration values.

    Exits:
        Prints missing keys and exits with code 1 if validation fails.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    config = dotenv_values(env_path)

    if not config:
        logger.error(f"Telemetry Validation Failure: Could not load config from '{env_path}'. File may be missing or empty.")
        sys.exit(1)

    missing = [key for key in REQUIRED_KEYS if not config.get(key)]
    if missing:
        logger.error(f"Telemetry Validation Failure: Missing required config keys: {', '.join(missing)}")
        logger.error(f"Please check your .env file at: {env_path}")
        sys.exit(1)

    # Strip trailing slashes from the URL for consistent usage
    config["CAMUNDA_URL"] = config["CAMUNDA_URL"].rstrip("/")

    # Parse comma-separated lists
    config["PROCESS_KEYS"] = [k.strip() for k in config["PROCESS_KEYS"].split(",") if k.strip()]
    
    tracked_vars = config.get("TRACKED_VARIABLES", "")
    config["TRACKED_VARIABLES"] = [v.strip() for v in tracked_vars.split(",") if v.strip()]

    return config
