"""
Tests for camunda_monitor.api — Camunda 7 REST API client.
"""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from camunda_monitor.api import (
    _build_auth,
    _engine_url,
    get_active_instances,
    get_incidents,
    check_process,
    REQUEST_TIMEOUT,
)


# ── Fixtures ─────────────────────────────────────────────────────────────────

MOCK_CONFIG = {
    "CAMUNDA_URL": "https://wflow.example.com:8443/camunda",
    "CAMUNDA_USERNAME": "admin",
    "CAMUNDA_PASSWORD": "secret",
    "PROCESS_KEYS": ["BatchProcess"],
    "TRACKED_VARIABLES": ["processKey"],
}

MOCK_INSTANCE = {
    "id": "abc-123",
    "definitionId": "BatchProcess:1:def-456",
    "businessKey": None,
    "ended": False,
    "suspended": False,
}

MOCK_INCIDENT = {
    "id": "inc-001",
    "incidentType": "failedJob",
    "incidentMessage": "Could not connect to external service",
    "activityId": "ServiceTask_1",
    "processInstanceId": "abc-123",
}


# ── Helper Tests ─────────────────────────────────────────────────────────────

class TestHelpers:
    """Tests for internal helper functions."""

    def test_build_auth_returns_tuple(self):
        auth = _build_auth(MOCK_CONFIG)
        assert auth == ("admin", "secret")

    def test_build_auth_tuple_length(self):
        auth = _build_auth(MOCK_CONFIG)
        assert len(auth) == 2

    def test_engine_url_construction(self):
        url = _engine_url(MOCK_CONFIG)
        assert url == "https://wflow.example.com:8443/camunda/engine-rest"

    def test_engine_url_no_double_slash(self):
        config = {**MOCK_CONFIG, "CAMUNDA_URL": "https://example.com/camunda"}
        url = _engine_url(config)
        assert "//" not in url.replace("https://", "")


# ── get_active_instances Tests ───────────────────────────────────────────────

class TestGetActiveInstances:
    """Tests for the get_active_instances function."""

    @patch("camunda_monitor.api.requests.get")
    def test_returns_list_of_instances(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = [MOCK_INSTANCE]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = get_active_instances(MOCK_CONFIG, "BatchProcess")

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["id"] == "abc-123"

    @patch("camunda_monitor.api.requests.get")
    def test_returns_empty_list_when_no_instances(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = get_active_instances(MOCK_CONFIG, "BatchProcess")

        assert result == []

    @patch("camunda_monitor.api.requests.get")
    def test_calls_correct_url(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        get_active_instances(MOCK_CONFIG, "BatchProcess")

        call_args = mock_get.call_args
        assert call_args[0][0] == "https://wflow.example.com:8443/camunda/engine-rest/process-instance"

    @patch("camunda_monitor.api.requests.get")
    def test_sends_correct_params(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        get_active_instances(MOCK_CONFIG, "LmdBatchProcess")

        call_kwargs = mock_get.call_args[1]
        assert call_kwargs["params"]["processDefinitionKey"] == "LmdBatchProcess"
        assert call_kwargs["params"]["active"] == "true"

    @patch("camunda_monitor.api.requests.get")
    def test_uses_basic_auth(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        get_active_instances(MOCK_CONFIG, "BatchProcess")

        call_kwargs = mock_get.call_args[1]
        assert call_kwargs["auth"] == ("admin", "secret")

    @patch("camunda_monitor.api.requests.get")
    def test_uses_configured_timeout(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        get_active_instances(MOCK_CONFIG, "BatchProcess")

        call_kwargs = mock_get.call_args[1]
        assert call_kwargs["timeout"] == REQUEST_TIMEOUT

    @patch("camunda_monitor.api.requests.get")
    def test_raises_on_http_error(self, mock_get):
        import requests as req
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = req.exceptions.HTTPError("500 Server Error")
        mock_get.return_value = mock_response

        with pytest.raises(req.exceptions.HTTPError):
            get_active_instances(MOCK_CONFIG, "BatchProcess")


# ── get_incidents Tests ──────────────────────────────────────────────────────

class TestGetIncidents:
    """Tests for the get_incidents function."""

    @patch("camunda_monitor.api.requests.get")
    def test_returns_list_of_incidents(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = [MOCK_INCIDENT]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = get_incidents(MOCK_CONFIG, "abc-123")

        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["incidentType"] == "failedJob"

    @patch("camunda_monitor.api.requests.get")
    def test_returns_empty_list_when_no_incidents(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = get_incidents(MOCK_CONFIG, "abc-123")

        assert result == []

    @patch("camunda_monitor.api.requests.get")
    def test_calls_incident_endpoint(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        get_incidents(MOCK_CONFIG, "abc-123")

        call_args = mock_get.call_args
        assert call_args[0][0].endswith("/engine-rest/incident")

    @patch("camunda_monitor.api.requests.get")
    def test_sends_process_instance_id_param(self, mock_get):
        mock_response = MagicMock()
        mock_response.json.return_value = []
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        get_incidents(MOCK_CONFIG, "xyz-789")

        call_kwargs = mock_get.call_args[1]
        assert call_kwargs["params"]["processInstanceId"] == "xyz-789"


# ── check_process Tests ──────────────────────────────────────────────────────

class TestCheckProcess:
    """Tests for the high-level check_process function."""

    @patch("camunda_monitor.api.get_process_variables")
    @patch("camunda_monitor.api.get_incidents")
    @patch("camunda_monitor.api.get_active_instances")
    def test_no_active_instances(self, mock_instances, mock_incidents, mock_vars):
        mock_instances.return_value = []

        result = check_process(MOCK_CONFIG, "BatchProcess")

        assert result["is_active"] is False
        assert result["instance_count"] == 0
        assert result["instance_id"] is None
        assert result["has_incident"] is False
        assert result["incidents"] == []
        mock_incidents.assert_not_called()

    @patch("camunda_monitor.api.get_process_variables")
    @patch("camunda_monitor.api.get_incidents")
    @patch("camunda_monitor.api.get_active_instances")
    def test_active_instances_no_incidents(self, mock_instances, mock_incidents, mock_vars):
        mock_instances.return_value = [MOCK_INSTANCE]
        mock_incidents.return_value = []
        mock_vars.return_value = {"processKey": "BP-01"}

        result = check_process(MOCK_CONFIG, "BatchProcess")

        assert result["is_active"] is True
        assert result["instance_count"] == 1
        assert result["instance_id"] == "abc-123"
        assert result["has_incident"] is False
        assert result["incidents"] == []
        assert result["variables"]["processKey"] == "BP-01"

    @patch("camunda_monitor.api.get_process_variables")
    @patch("camunda_monitor.api.get_incidents")
    @patch("camunda_monitor.api.get_active_instances")
    def test_active_instances_with_incident(self, mock_instances, mock_incidents, mock_vars):
        mock_instances.return_value = [MOCK_INSTANCE]
        mock_incidents.return_value = [MOCK_INCIDENT]
        mock_vars.return_value = {"processKey": "BP-01"}

        result = check_process(MOCK_CONFIG, "BatchProcess")

        assert result["is_active"] is True
        assert result["has_incident"] is True
        assert len(result["incidents"]) == 1
        assert result["incidents"][0]["type"] == "failedJob"
        assert result["incidents"][0]["message"] == "Could not connect to external service"
        assert result["incidents"][0]["activity_id"] == "ServiceTask_1"
        assert result["variables"]["processKey"] == "BP-01"

    @patch("camunda_monitor.api.get_process_variables")
    @patch("camunda_monitor.api.get_incidents")
    @patch("camunda_monitor.api.get_active_instances")
    def test_multiple_active_instances(self, mock_instances, mock_incidents, mock_vars):
        instance_2 = {**MOCK_INSTANCE, "id": "def-456"}
        mock_instances.return_value = [MOCK_INSTANCE, instance_2]
        mock_incidents.return_value = []
        mock_vars.return_value = {"processKey": "BP-01"}

        result = check_process(MOCK_CONFIG, "BatchProcess")

        assert result["instance_count"] == 2
        # Should check incidents on the FIRST instance only
        assert result["instance_id"] == "abc-123"

    @patch("camunda_monitor.api.get_process_variables")
    @patch("camunda_monitor.api.get_incidents")
    @patch("camunda_monitor.api.get_active_instances")
    def test_multiple_incidents(self, mock_instances, mock_incidents, mock_vars):
        incident_2 = {
            **MOCK_INCIDENT,
            "id": "inc-002",
            "incidentType": "failedExternalTask",
            "incidentMessage": "Timeout connecting to payment gateway",
            "activityId": "ServiceTask_2",
        }
        mock_instances.return_value = [MOCK_INSTANCE]
        mock_incidents.return_value = [MOCK_INCIDENT, incident_2]
        mock_vars.return_value = {"processKey": "BP-01"}

        result = check_process(MOCK_CONFIG, "BatchProcess")

        assert len(result["incidents"]) == 2
        assert result["incidents"][1]["type"] == "failedExternalTask"

    @patch("camunda_monitor.api.get_process_variables")
    @patch("camunda_monitor.api.get_incidents")
    @patch("camunda_monitor.api.get_active_instances")
    def test_incident_with_missing_fields_uses_defaults(self, mock_instances, mock_incidents, mock_vars):
        sparse_incident = {"id": "inc-003"}  # No incidentType, incidentMessage, activityId
        mock_instances.return_value = [MOCK_INSTANCE]
        mock_incidents.return_value = [sparse_incident]
        mock_vars.return_value = {"processKey": "BP-01"}

        result = check_process(MOCK_CONFIG, "BatchProcess")

        assert result["has_incident"] is True
        assert result["incidents"][0]["type"] == "Unknown"
        assert result["incidents"][0]["message"] == "No message"
        assert result["incidents"][0]["activity_id"] == ""
