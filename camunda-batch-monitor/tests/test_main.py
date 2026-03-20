"""
Tests for camunda_monitor.__main__ — CLI entry point and main flow.
"""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock, call

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from camunda_monitor.__main__ import parse_args, main


# ── Fixtures ─────────────────────────────────────────────────────────────────

MOCK_CONFIG = {
    "CAMUNDA_URL": "https://example.com/camunda",
    "CAMUNDA_USERNAME": "admin",
    "CAMUNDA_PASSWORD": "secret",
    "GOOGLE_CHAT_WEBHOOK": "https://chat.googleapis.com/test",
    "PROCESS_KEYS": ["BatchProcess", "LmdBatchProcess"],
}


# ── parse_args Tests ─────────────────────────────────────────────────────────

class TestParseArgs:
    """Tests for CLI argument parsing."""

    def test_default_config_path(self):
        with patch("sys.argv", ["camunda_monitor"]):
            args = parse_args()
            assert args.config is not None
            assert ".env.example" in args.config

    def test_custom_config_path(self):
        with patch("sys.argv", ["camunda_monitor", "--config", "/my/path/config.env"]):
            args = parse_args()
            assert args.config == "/my/path/config.env"


# ── main() Flow Tests ────────────────────────────────────────────────────────

class TestMainFlow:
    """Tests for the main application flow."""

    @patch("camunda_monitor.__main__.send_status")
    @patch("camunda_monitor.__main__.check_process")
    @patch("camunda_monitor.__main__.load_config")
    @patch("camunda_monitor.__main__.parse_args")
    def test_batch_process_active_no_incidents(self, mock_args, mock_config, mock_check, mock_send):
        mock_args.return_value = MagicMock(config="test.env")
        mock_config.return_value = MOCK_CONFIG
        mock_check.return_value = {
            "is_active": True,
            "instance_count": 2,
            "instance_id": "abc-123",
            "has_incident": False,
            "incidents": [],
            "variables": {"processKey": "val"},
            "all_processes": ["BatchProcess", "LmdBatchProcess"]
        }
    
        main()
    
        # Should only check BatchProcess (stops at first active)
        mock_check.assert_called_once_with(MOCK_CONFIG, "BatchProcess")
        mock_send.assert_called_once_with(
            webhook_url="https://chat.googleapis.com/test",
            process_status="BatchProcess",
            is_active=True,
            has_incident=False,
            incident_details=[],
            instance_count=2,
            process_variables={"processKey": "val"},
            all_processes=["BatchProcess", "LmdBatchProcess"]
        )

    @patch("camunda_monitor.__main__.send_status")
    @patch("camunda_monitor.__main__.check_process")
    @patch("camunda_monitor.__main__.load_config")
    @patch("camunda_monitor.__main__.parse_args")
    def test_falls_back_to_lmd_when_batch_inactive(self, mock_args, mock_config, mock_check, mock_send):
        mock_args.return_value = MagicMock(config="test.env")
        mock_config.return_value = MOCK_CONFIG

        # BatchProcess inactive, LmdBatchProcess active
        mock_check.side_effect = [
            {"is_active": False, "instance_count": 0, "instance_id": None, "has_incident": False, "incidents": []},
            {"is_active": True, "instance_count": 1, "instance_id": "def-456", "has_incident": False, "incidents": []},
        ]

        main()

        assert mock_check.call_count == 2
        mock_send.assert_called_once()
        send_kwargs = mock_send.call_args[1]
        assert send_kwargs["process_status"] == "LmdBatchProcess"
        assert send_kwargs["is_active"] is True

    @patch("camunda_monitor.__main__.send_status")
    @patch("camunda_monitor.__main__.check_process")
    @patch("camunda_monitor.__main__.load_config")
    @patch("camunda_monitor.__main__.parse_args")
    def test_both_processes_completed(self, mock_args, mock_config, mock_check, mock_send):
        mock_args.return_value = MagicMock(config="test.env")
        mock_config.return_value = MOCK_CONFIG

        # Both processes inactive
        mock_check.return_value = {
            "is_active": False, "instance_count": 0, "instance_id": None,
            "has_incident": False, "incidents": [],
        }

        main()

        assert mock_check.call_count == 2
        send_kwargs = mock_send.call_args[1]
        assert send_kwargs["process_status"] == "Batch Completed!"
        assert send_kwargs["is_active"] is False

    @patch("camunda_monitor.__main__.send_status")
    @patch("camunda_monitor.__main__.check_process")
    @patch("camunda_monitor.__main__.load_config")
    @patch("camunda_monitor.__main__.parse_args")
    def test_incident_detected(self, mock_args, mock_config, mock_check, mock_send):
        mock_args.return_value = MagicMock(config="test.env")
        mock_config.return_value = MOCK_CONFIG

        incidents = [{"type": "failedJob", "message": "Error", "activity_id": "Task_1"}]
        mock_check.return_value = {
            "is_active": True, "instance_count": 1, "instance_id": "abc-123",
            "has_incident": True, "incidents": incidents,
        }

        main()

        send_kwargs = mock_send.call_args[1]
        assert send_kwargs["has_incident"] is True
        assert len(send_kwargs["incident_details"]) == 1

    @patch("camunda_monitor.__main__.send_error")
    @patch("camunda_monitor.__main__.check_process")
    @patch("camunda_monitor.__main__.load_config")
    @patch("camunda_monitor.__main__.parse_args")
    def test_sends_error_card_on_exception(self, mock_args, mock_config, mock_check, mock_send_error):
        mock_args.return_value = MagicMock(config="test.env")
        mock_config.return_value = MOCK_CONFIG
        mock_check.side_effect = Exception("API unreachable")

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1
        mock_send_error.assert_called_once()
        error_msg = mock_send_error.call_args[0][1]
        assert "API unreachable" in error_msg

    @patch("camunda_monitor.__main__.send_error")
    @patch("camunda_monitor.__main__.check_process")
    @patch("camunda_monitor.__main__.load_config")
    @patch("camunda_monitor.__main__.parse_args")
    def test_exits_with_code_1_on_exception(self, mock_args, mock_config, mock_check, mock_send_error):
        mock_args.return_value = MagicMock(config="test.env")
        mock_config.return_value = MOCK_CONFIG
        mock_check.side_effect = RuntimeError("Broken")

        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1
