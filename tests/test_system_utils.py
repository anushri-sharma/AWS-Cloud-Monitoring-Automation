"""
Tests for system_utils.py

We don't want tests to depend on the *actual* CPU/memory/disk usage of
whatever machine runs them (that would make tests flaky), so we mock
psutil's functions and just check that our code wires them together
correctly.
"""

from unittest.mock import patch, MagicMock
from system_utils import get_system_details


@patch("system_utils.psutil")
def test_get_system_details_returns_expected_keys(mock_psutil):
    # Arrange: make psutil return fixed, predictable values
    mock_psutil.cpu_percent.return_value = 12.5
    mock_psutil.virtual_memory.return_value = MagicMock(percent=45.0)
    mock_psutil.disk_usage.return_value = MagicMock(percent=70.0)

    # Act
    result = get_system_details()

    # Assert
    assert result == {"cpu": 12.5, "memory": 45.0, "disk": 70.0}


@patch("system_utils.psutil")
def test_get_system_details_calls_psutil_correctly(mock_psutil):
    mock_psutil.cpu_percent.return_value = 0
    mock_psutil.virtual_memory.return_value = MagicMock(percent=0)
    mock_psutil.disk_usage.return_value = MagicMock(percent=0)

    get_system_details()

    mock_psutil.cpu_percent.assert_called_once_with(interval=1)
    mock_psutil.disk_usage.assert_called_once_with("/")
