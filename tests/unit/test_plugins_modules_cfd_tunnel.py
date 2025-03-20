from __future__ import absolute_import, division, print_function


__metaclass__ = type

from unittest.mock import MagicMock, patch

import pytest

from ansible_collections.code_kaizen.cloudflare.plugins.modules import cfd_tunnel


@pytest.fixture
def mock_module():
    """Create a mock AnsibleModule."""
    mock = MagicMock()
    mock.check_mode = False
    mock.params = {
        "api_token": "test-token",
        "account_id": "test-account",
        "name": "test-tunnel",
        "config_src": "local",
        "tunnel_secret": "test-secret",
        "state": "present",
    }
    # Configure exit_json and fail_json to raise SystemExit
    mock.exit_json.side_effect = SystemExit()
    mock.fail_json.side_effect = SystemExit()
    return mock


@pytest.fixture
def mock_response():
    """Create a mock response object."""
    mock = MagicMock()
    mock.status_code = 200
    mock.raise_for_status.return_value = None
    mock.json.return_value = {"result": [], "result_info": {"page": 1, "total_pages": 1}}
    return mock


class TestCfdTunnel:
    """Tests for the cfd_tunnel module."""

    def test_fetch_tunnel_success(self, mock_module, mock_response):
        """Test successful tunnel fetch."""
        expected_tunnel = {
            "id": "tunnel-id",
            "name": "test-tunnel",
            "config_src": "local",
        }
        mock_response.json.return_value = {
            "result": [expected_tunnel],
            "result_info": {"page": 1, "total_pages": 1},
        }

        with patch("requests.get", return_value=mock_response):
            result = cfd_tunnel.fetch_tunnel(
                mock_module,
                "test-token",
                "test-account",
                "test-tunnel",
            )

        assert result == expected_tunnel

    def test_create_tunnel_check_mode(self, mock_module):
        """Test create tunnel in check mode."""
        mock_module.check_mode = True

        with pytest.raises(SystemExit) as exc_info:
            cfd_tunnel.create_tunnel(
                mock_module,
                "test-token",
                "test-account",
                "test-tunnel",
                "local",
                "test-secret",
            )

        mock_module.exit_json.assert_called_once_with(
            changed=True,
            msg="Would have created tunnel (check mode)",
        )

    def test_delete_tunnel_check_mode(self, mock_module, mock_response):
        """Test delete tunnel in check mode."""
        mock_module.check_mode = True
        mock_response.json.return_value = {
            "result": [
                {
                    "id": "tunnel-id",
                    "name": "test-tunnel",
                },
            ],
            "result_info": {"page": 1, "total_pages": 1},
        }

        with patch("requests.get", return_value=mock_response):
            with pytest.raises(SystemExit):
                cfd_tunnel.delete_tunnel(
                    mock_module,
                    "test-token",
                    "test-account",
                    "test-tunnel",
                )

        mock_module.exit_json.assert_called_once_with(
            changed=True,
            msg="Would have deleted tunnel (check mode)",
        )

    def test_delete_nonexistent_tunnel(self, mock_module, mock_response):
        """Test deleting a tunnel that doesn't exist."""
        mock_response.json.return_value = {
            "result": [],
            "result_info": {"page": 1, "total_pages": 1},
        }

        with patch("requests.get", return_value=mock_response):
            with pytest.raises(SystemExit):
                cfd_tunnel.delete_tunnel(
                    mock_module,
                    "test-token",
                    "test-account",
                    "test-tunnel",
                )

        mock_module.exit_json.assert_called_once_with(
            changed=False,
            msg="Tunnel does not exist",
        )
