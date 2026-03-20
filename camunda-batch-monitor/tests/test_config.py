"""
Tests for camunda_monitor.config — config loading and validation.
"""

import os
import tempfile
import pytest
import sys

# Add src to path so imports work when running pytest from project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from camunda_monitor.config import load_config, REQUIRED_KEYS


# ── Fixtures ─────────────────────────────────────────────────────────────────

def _write_env(tmpdir, content: str) -> str:
    """Write content to a temp .env file and return its path."""
    env_file = os.path.join(tmpdir, "test.env")
    with open(env_file, "w") as f:
        f.write(content)
    return env_file


VALID_ENV = (
    "CAMUNDA_URL=https://example.com/camunda\n"
    "CAMUNDA_USERNAME=admin\n"
    "CAMUNDA_PASSWORD=secret\n"
    "GOOGLE_CHAT_WEBHOOK=https://chat.googleapis.com/v1/spaces/test\n"
    "PROCESS_KEYS=BatchProcess,LmdBatchProcess\n"
    "TRACKED_VARIABLES=processKey,CCAT,jobId\n"
)


# ── Tests ────────────────────────────────────────────────────────────────────

class TestLoadConfigSuccess:
    """Tests for successful config loading."""

    def test_loads_all_required_keys(self, tmp_path):
        env_file = _write_env(tmp_path, VALID_ENV)
        config = load_config(env_file)

        assert config["CAMUNDA_URL"] == "https://example.com/camunda"
        assert config["CAMUNDA_USERNAME"] == "admin"
        assert config["CAMUNDA_PASSWORD"] == "secret"
        assert config["GOOGLE_CHAT_WEBHOOK"] == "https://chat.googleapis.com/v1/spaces/test"

    def test_strips_trailing_slash_from_url(self, tmp_path):
        content = VALID_ENV.replace(
            "https://example.com/camunda",
            "https://example.com/camunda/"
        )
        env_file = _write_env(tmp_path, content)
        config = load_config(env_file)

        assert not config["CAMUNDA_URL"].endswith("/")
        assert config["CAMUNDA_URL"] == "https://example.com/camunda"

    def test_strips_multiple_trailing_slashes(self, tmp_path):
        content = VALID_ENV.replace(
            "https://example.com/camunda",
            "https://example.com/camunda///"
        )
        env_file = _write_env(tmp_path, content)
        config = load_config(env_file)

        assert config["CAMUNDA_URL"] == "https://example.com/camunda"

    def test_preserves_extra_keys(self, tmp_path):
        content = VALID_ENV + "EXTRA_KEY=bonus_value\n"
        env_file = _write_env(tmp_path, content)
        config = load_config(env_file)

        assert config["EXTRA_KEY"] == "bonus_value"

    def test_returns_dict_type(self, tmp_path):
        env_file = _write_env(tmp_path, VALID_ENV)
        config = load_config(env_file)

        assert isinstance(config, dict)


class TestLoadConfigFailure:
    """Tests for config validation failures (should sys.exit)."""

    def test_exits_on_missing_file(self):
        with pytest.raises(SystemExit) as exc_info:
            load_config("/nonexistent/path/fake.env")
        assert exc_info.value.code == 1

    def test_exits_on_empty_file(self, tmp_path):
        env_file = _write_env(tmp_path, "")
        with pytest.raises(SystemExit) as exc_info:
            load_config(env_file)
        assert exc_info.value.code == 1

    def test_exits_on_missing_camunda_url(self, tmp_path):
        content = (
            "CAMUNDA_USERNAME=admin\n"
            "CAMUNDA_PASSWORD=secret\n"
            "GOOGLE_CHAT_WEBHOOK=https://hook\n"
        )
        env_file = _write_env(tmp_path, content)
        with pytest.raises(SystemExit) as exc_info:
            load_config(env_file)
        assert exc_info.value.code == 1

    def test_exits_on_missing_username(self, tmp_path):
        content = (
            "CAMUNDA_URL=https://example.com\n"
            "CAMUNDA_PASSWORD=secret\n"
            "GOOGLE_CHAT_WEBHOOK=https://hook\n"
        )
        env_file = _write_env(tmp_path, content)
        with pytest.raises(SystemExit) as exc_info:
            load_config(env_file)
        assert exc_info.value.code == 1

    def test_exits_on_missing_password(self, tmp_path):
        content = (
            "CAMUNDA_URL=https://example.com\n"
            "CAMUNDA_USERNAME=admin\n"
            "GOOGLE_CHAT_WEBHOOK=https://hook\n"
        )
        env_file = _write_env(tmp_path, content)
        with pytest.raises(SystemExit) as exc_info:
            load_config(env_file)
        assert exc_info.value.code == 1

    def test_exits_on_missing_webhook(self, tmp_path):
        content = (
            "CAMUNDA_URL=https://example.com\n"
            "CAMUNDA_USERNAME=admin\n"
            "CAMUNDA_PASSWORD=secret\n"
        )
        env_file = _write_env(tmp_path, content)
        with pytest.raises(SystemExit) as exc_info:
            load_config(env_file)
        assert exc_info.value.code == 1

    def test_exits_on_empty_value_for_required_key(self, tmp_path):
        content = (
            "CAMUNDA_URL=\n"
            "CAMUNDA_USERNAME=admin\n"
            "CAMUNDA_PASSWORD=secret\n"
            "GOOGLE_CHAT_WEBHOOK=https://hook\n"
            "PROCESS_KEYS=BatchProcess\n"
        )
        env_file = _write_env(tmp_path, content)
        with pytest.raises(SystemExit) as exc_info:
            load_config(env_file)
        assert exc_info.value.code == 1


class TestRequiredKeys:
    """Verify that REQUIRED_KEYS constant is correct."""

    def test_contains_all_expected_keys(self):
        expected = {"CAMUNDA_URL", "CAMUNDA_USERNAME", "CAMUNDA_PASSWORD", "GOOGLE_CHAT_WEBHOOK", "PROCESS_KEYS"}
        assert set(REQUIRED_KEYS) == expected

    def test_is_list(self):
        assert isinstance(REQUIRED_KEYS, list)
