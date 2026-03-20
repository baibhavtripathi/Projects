"""
Camunda 7 REST API client for querying process instances and incidents.

Security Note:
    SSL certificate verification is disabled. Since this runs on a secured internal
    network, the risk is accepted. However, it is recommended to use your internal
    CA bundle instead of disabling verification entirely:
    verify='/path/to/company-ca-bundle.pem'
"""

import urllib3
import requests

# Suppress InsecureRequestWarning for self-signed certs (common in internal Camunda deployments)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Timeout for all API calls (connect, read) in seconds
REQUEST_TIMEOUT = 15


def _build_auth(config: dict) -> tuple:
    """Build HTTP Basic Auth tuple from config."""
    return (config["CAMUNDA_USERNAME"], config["CAMUNDA_PASSWORD"])


def _engine_url(config: dict) -> str:
    """Build the base engine-rest URL."""
    return f"{config['CAMUNDA_URL']}/engine-rest"


def get_active_instances(config: dict, process_key: str) -> list:
    """
    Query Camunda 7 for active process instances of a given process definition key.

    Endpoint:
        GET /engine-rest/process-instance
            ?processDefinitionKey={key}
            &active=true

    Args:
        config: Application config dict.
        process_key: The process definition key (e.g. 'BatchProcess').

    Returns:
        List of active process instance dicts. Empty list if none are running.

    Raises:
        requests.RequestException on network/API errors.
    """
    url = f"{_engine_url(config)}/process-instance"
    params = {
        "processDefinitionKey": process_key,
        "active": "true",
    }

    response = requests.get(
        url,
        params=params,
        auth=_build_auth(config),
        timeout=REQUEST_TIMEOUT,
        verify=False,  # Self-signed certs on internal servers
    )
    response.raise_for_status()
    return response.json()


def get_incidents(config: dict, process_instance_id: str) -> list:
    """
    Query Camunda 7 for incidents on a specific process instance.

    Endpoint:
        GET /engine-rest/incident?processInstanceId={id}

    Args:
        config: Application config dict.
        process_instance_id: The process instance ID to check.

    Returns:
        List of incident dicts. Empty list if no incidents.

    Raises:
        requests.RequestException on network/API errors.
    """
    url = f"{_engine_url(config)}/incident"
    params = {
        "processInstanceId": process_instance_id,
    }

    response = requests.get(
        url,
        params=params,
        auth=_build_auth(config),
        timeout=REQUEST_TIMEOUT,
        verify=False,
    )
    response.raise_for_status()
    return response.json()


def get_process_variables(config: dict, process_instance_id: str) -> dict:
    """
    Query Camunda 7 for all variables on a specific process instance.

    Endpoint:
        GET /engine-rest/process-instance/{id}/variables

    Returns a dict mapping variable names to their values.
    """
    url = f"{_engine_url(config)}/process-instance/{process_instance_id}/variables"
    response = requests.get(
        url,
        auth=_build_auth(config),
        timeout=REQUEST_TIMEOUT,
        verify=False,
    )
    if response.status_code == 200:
        data = response.json()
        return {k: v.get("value") for k, v in data.items()}
    return {}


def check_process(config: dict, process_key: str) -> dict:
    """
    High-level check: are there active instances for this process?
    If so, also check for incidents and tracked variables on the first active instance.

    Args:
        config: Application config dict.
        process_key: Process definition key to check.

    Returns:
        dict with keys:
            - is_active (bool)
            - instance_count (int)
            - instance_id (str | None)
            - has_incident (bool)
            - incidents (list of dicts with 'type' and 'message')
            - variables (dict of tracked process variables mapped to their values)
    """
    instances = get_active_instances(config, process_key)

    result = {
        "is_active": len(instances) > 0,
        "instance_count": len(instances),
        "instance_id": None,
        "has_incident": False,
        "incidents": [],
        "variables": {},
    }

    if instances:
        # Check the first active instance for incidents and variables
        first_instance = instances[0]
        result["instance_id"] = first_instance.get("id")

        # Fetch incidents
        raw_incidents = get_incidents(config, result["instance_id"])
        if raw_incidents:
            result["has_incident"] = True
            result["incidents"] = [
                {
                    "type": inc.get("incidentType", "Unknown"),
                    "message": inc.get("incidentMessage", "No message"),
                    "activity_id": inc.get("activityId", ""),
                }
                for inc in raw_incidents
            ]
            
        # Fetch variables (only the ones configured in .env TRACKED_VARIABLES)
        tracked_vars = config.get("TRACKED_VARIABLES", [])
        if tracked_vars:
            all_vars = get_process_variables(config, result["instance_id"])
            for t_var in tracked_vars:
                result["variables"][t_var] = all_vars.get(t_var, "Not found")

    return result
