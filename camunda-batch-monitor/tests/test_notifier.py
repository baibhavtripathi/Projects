"""
Tests for camunda_monitor.notifier — Google Chat webhook sender.
"""

import os
import sys
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from camunda_monitor.notifier import (
    _build_status_card,
    _build_error_card,
    send_status,
    send_error,
)


# ── Fixtures ─────────────────────────────────────────────────────────────────

WEBHOOK_URL = "https://chat.googleapis.com/v1/spaces/test/messages?key=test&token=test"

SAMPLE_INCIDENTS = [
    {
        "type": "failedJob",
        "message": "Connection timeout",
        "activity_id": "ServiceTask_1",
    },
]


# ── _build_status_card Tests ─────────────────────────────────────────────────

class TestBuildStatusCard:
    """Tests for building Card v2 payloads."""

    def test_running_card_has_correct_title(self):
        card = _build_status_card("BatchProcess", True, False, [], 3, {})
        header = card["cardsV2"][0]["card"]["header"]
        assert "BatchProcess" in header["title"]
        assert "📊" in header["title"]

    def test_running_card_shows_instance_count(self):
        card = _build_status_card("BatchProcess", True, False, [], 5, {})
        text = card["cardsV2"][0]["card"]["sections"][0]["widgets"][0]["textParagraph"]["text"]
        assert "5" in text

    def test_completed_card_has_correct_title(self):
        card = _build_status_card("Batch Completed!", False, False, [], 0, {})
        header = card["cardsV2"][0]["card"]["header"]
        assert "✅" in header["title"]
        assert "Completed" in header["title"]

    def test_completed_card_mentions_both_processes(self):
        card = _build_status_card("Batch Completed!", False, False, [], 0, {})
        text = card["cardsV2"][0]["card"]["sections"][0]["widgets"][0]["textParagraph"]["text"]
        assert "All configured processes are finished" in text

    def test_incident_card_has_urgent_title(self):
        card = _build_status_card("BatchProcess", True, True, SAMPLE_INCIDENTS, 1, {})
        header = card["cardsV2"][0]["card"]["header"]
        assert "🚨" in header["title"]
        assert "Incident" in header["title"]

    def test_incident_card_contains_error_details(self):
        card = _build_status_card("BatchProcess", True, True, SAMPLE_INCIDENTS, 1, {})
        text = card["cardsV2"][0]["card"]["sections"][0]["widgets"][0]["textParagraph"]["text"]
        assert "failedJob" in text
        assert "Connection timeout" in text
        assert "ServiceTask_1" in text

    def test_incident_card_without_activity_id(self):
        incidents = [{"type": "failedJob", "message": "Error", "activity_id": ""}]
        card = _build_status_card("BatchProcess", True, True, incidents, 1, {})
        text = card["cardsV2"][0]["card"]["sections"][0]["widgets"][0]["textParagraph"]["text"]
        # Should NOT contain " (at )" when activity_id is empty
        assert "(at )" not in text

    def test_incident_card_with_multiple_incidents(self):
        incidents = [
            {"type": "failedJob", "message": "Error 1", "activity_id": "Task_A"},
            {"type": "failedExternalTask", "message": "Error 2", "activity_id": "Task_B"},
        ]
        card = _build_status_card("BatchProcess", True, True, incidents, 1, {})
        text = card["cardsV2"][0]["card"]["sections"][0]["widgets"][0]["textParagraph"]["text"]
        assert "failedJob" in text
        assert "failedExternalTask" in text
        assert "Error 1" in text
        assert "Error 2" in text

    def test_incident_card_with_empty_details_list(self):
        card = _build_status_card("BatchProcess", True, True, [], 1, {})
        text = card["cardsV2"][0]["card"]["sections"][0]["widgets"][0]["textParagraph"]["text"]
        assert "no details available" in text

    def test_card_has_valid_structure(self):
        card = _build_status_card("BatchProcess", True, False, [], 1, {})
        assert "cardsV2" in card
        assert len(card["cardsV2"]) == 1
        inner = card["cardsV2"][0]
        assert "cardId" in inner
        assert "card" in inner
        assert "header" in inner["card"]
        assert "sections" in inner["card"]

    def test_card_has_image_url(self):
        card = _build_status_card("BatchProcess", True, False, [], 1, {})
        header = card["cardsV2"][0]["card"]["header"]
        assert "imageUrl" in header
        assert header["imageUrl"].startswith("https://")

    def test_subtitle_contains_timestamp(self):
        card = _build_status_card("BatchProcess", True, False, [], 1, {})
        subtitle = card["cardsV2"][0]["card"]["header"]["subtitle"]
        # Should contain date-like pattern (YYYY-MM-DD)
        current_year = str(datetime.now().year)
        assert current_year in subtitle


# ── _build_error_card Tests ──────────────────────────────────────────────────

class TestBuildErrorCard:
    """Tests for error card payload."""

    def test_error_card_has_failure_title(self):
        card = _build_error_card("Something went wrong")
        header = card["cardsV2"][0]["card"]["header"]
        assert "❌" in header["title"]
        assert "Failed" in header["title"]

    def test_error_card_contains_error_message(self):
        card = _build_error_card("Connection refused")
        text = card["cardsV2"][0]["card"]["sections"][0]["widgets"][0]["textParagraph"]["text"]
        assert "Connection refused" in text

    def test_error_card_has_valid_structure(self):
        card = _build_error_card("test error")
        assert "cardsV2" in card
        assert card["cardsV2"][0]["cardId"] == "camunda-monitor-error"


# ── send_status Tests ────────────────────────────────────────────────────────

class TestSendStatus:
    """Tests for the send_status function."""

    @patch("camunda_monitor.notifier.requests.post")
    def test_sends_post_to_webhook(self, mock_post):
        mock_post.return_value = MagicMock(status_code=200)

        send_status(WEBHOOK_URL, "BatchProcess", True, False, [], 1)

        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert call_args[0][0] == WEBHOOK_URL

    @patch("camunda_monitor.notifier.requests.post")
    def test_sends_json_payload(self, mock_post):
        mock_post.return_value = MagicMock(status_code=200)

        send_status(WEBHOOK_URL, "BatchProcess", True, False, [], 1)

        call_kwargs = mock_post.call_args[1]
        assert "json" in call_kwargs
        assert "cardsV2" in call_kwargs["json"]

    @patch("camunda_monitor.notifier.requests.post")
    def test_uses_timeout(self, mock_post):
        mock_post.return_value = MagicMock(status_code=200)

        send_status(WEBHOOK_URL, "BatchProcess", True, False, [], 1)

        call_kwargs = mock_post.call_args[1]
        assert call_kwargs["timeout"] == 10

    @patch("camunda_monitor.notifier.requests.post")
    def test_prints_warning_on_non_200(self, mock_post, caplog):
        mock_post.return_value = MagicMock(status_code=403, text="Forbidden")

        send_status(WEBHOOK_URL, "BatchProcess", True, False, [], 1)

        captured = caplog.text
        assert "403" in caplog.text

    @patch("camunda_monitor.notifier.requests.post")
    def test_prints_success_on_200(self, mock_post, caplog):
        import logging
        caplog.set_level(logging.INFO)
        mock_post.return_value = MagicMock(status_code=200)

        send_status(WEBHOOK_URL, "BatchProcess", True, False, [], 1)

        captured = caplog.text
        assert "sent successfully" in caplog.text


# ── send_error Tests ─────────────────────────────────────────────────────────

class TestSendError:
    """Tests for the send_error function."""

    @patch("camunda_monitor.notifier.requests.post")
    def test_sends_error_card(self, mock_post):
        mock_post.return_value = MagicMock(status_code=200)

        send_error(WEBHOOK_URL, "Test failure")

        mock_post.assert_called_once()
        payload = mock_post.call_args[1]["json"]
        assert payload["cardsV2"][0]["cardId"] == "camunda-monitor-error"

    @patch("camunda_monitor.notifier.requests.post")
    def test_handles_post_exception_gracefully(self, mock_post, caplog):
        mock_post.side_effect = Exception("Network unreachable")

        # Should NOT raise — it prints a warning instead
        send_error(WEBHOOK_URL, "Test failure")

        captured = caplog.text
        assert "Could not connect" in caplog.text

    @patch("camunda_monitor.notifier.requests.post")
    def test_prints_warning_on_non_200(self, mock_post, caplog):
        mock_post.return_value = MagicMock(status_code=500, text="Internal Server Error")

        send_error(WEBHOOK_URL, "Test failure")

        captured = caplog.text
        assert "500" in caplog.text
