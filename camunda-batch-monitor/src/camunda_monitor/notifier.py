"""
Google Chat notifier — sends formatted Card v2 messages via webhook.
"""

from datetime import datetime
import requests


def _build_status_card(process_status: str, is_active: bool, has_incident: bool,
                       incident_details: list, instance_count: int,
                       process_variables: dict, all_processes: list = None) -> dict:
    """Build a Google Chat Card v2 payload based on process status."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Format tracked variables HTML block if any exist
    variables_html = ""
    if process_variables:
        variables_html = "<br/><b>Process Variables:</b><br/>"
        for k, v in process_variables.items():
            variables_html += f"• <b>{k}</b>: {v}<br/>"

    if has_incident:
        # ── Incident Card ────────────────────────────────────────────────
        header_title = "🚨 URGENT: Camunda Incident"
        header_subtitle = f"{process_status} — {now}"

        incident_lines = []
        for inc in incident_details:
            activity = f" (at {inc['activity_id']})" if inc.get("activity_id") else ""
            incident_lines.append(
                f"• <b>{inc['type']}</b>{activity}<br/>{inc['message']}"
            )
        status_text = "<br/>".join(incident_lines) if incident_lines else "Incident detected (no details available)."
        status_text += "<br/>" + variables_html

    elif not is_active:
        # ── Completed Card ───────────────────────────────────────────────
        header_title = "✅ Batch Completed"
        header_subtitle = now
        
        if all_processes:
            names = ", ".join([f"<b>{p}</b>" for p in all_processes])
            status_text = f"{names} finished. No active instances found."
        else:
            status_text = "All configured processes are finished. No active instances found."

    else:
        # ── Running Card ─────────────────────────────────────────────────
        header_title = f"📊 Batch Status — {process_status}"
        header_subtitle = now
        status_text = (
            f"Process <b>{process_status}</b> is currently running."
            f"<br/>Active instances: <b>{instance_count}</b>"
            f"<br/>{variables_html}"
        )

    widgets = [{"textParagraph": {"text": status_text}}]

    return {
        "cardsV2": [{
            "cardId": "camunda-batch-status",
            "card": {
                "header": {
                    "title": header_title,
                    "subtitle": header_subtitle,
                    "imageUrl": "https://fonts.gstatic.com/s/i/short-term/release/materialsymbolsoutlined/monitor_heart/default/48px.svg",
                    "imageType": "CIRCLE",
                },
                "sections": [{"widgets": widgets}],
            },
        }],
    }


def _build_error_card(error_message: str) -> dict:
    """Build a Google Chat Card v2 payload for script failures."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return {
        "cardsV2": [{
            "cardId": "camunda-monitor-error",
            "card": {
                "header": {
                    "title": "❌ Monitor Script Failed",
                    "subtitle": now,
                    "imageType": "CIRCLE",
                },
                "sections": [{
                    "widgets": [{
                        "textParagraph": {
                            "text": f"<b>Error:</b> {error_message}"
                        }
                    }],
                }],
            },
        }],
    }


def send_status(webhook_url: str, process_status: str, is_active: bool,
                has_incident: bool, incident_details: list,
                instance_count: int = 0, process_variables: dict = None,
                all_processes: list = None) -> None:
    """
    Send a formatted status card to Google Chat.

    Args:
        webhook_url: Google Chat webhook URL.
        process_status: Name of the process or 'Batch Completed!'.
        is_active: Whether a process is currently running.
        has_incident: Whether incidents were detected.
        incident_details: List of incident dicts with 'type', 'message', 'activity_id'.
        instance_count: Number of active instances.
        process_variables: Dict of process variable keys mapped to their current values.
        all_processes: List of all checked process definition keys, for reporting.
    """
    if process_variables is None:
        process_variables = {}
        
    payload = _build_status_card(
        process_status, is_active, has_incident, incident_details, 
        instance_count, process_variables, all_processes
    )

    import logging
    logger = logging.getLogger(__name__)
    
    resp = requests.post(webhook_url, json=payload, timeout=10)
    if resp.status_code != 200:
        logger.warning(f"Chat webhook error {resp.status_code}: {resp.text}")
    else:
        logger.info(f"Google Chat notification sent successfully for state: {process_status}")


def send_error(webhook_url: str, error_message: str) -> None:
    """
    Send a script failure alert to Google Chat.

    Args:
        webhook_url: Google Chat webhook URL.
        error_message: The error string to report.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    payload = _build_error_card(error_message)

    try:
        resp = requests.post(webhook_url, json=payload, timeout=10)
        if resp.status_code != 200:
            logger.warning(f"Chat webhook error {resp.status_code}: {resp.text}")
        else:
            logger.info("Google Chat fallback error notification dispatched.")
    except Exception as e:
        # Last resort: if even the error notification fails
        logger.critical(f"NETWORK FAILURE: Could not connect to Google Chat webhook to dispatch error: {e}")
