import pytest
from unittest.mock import patch, mock_open, MagicMock
from pathlib import Path
from src.api.owner_ops import stream_log


def test_stream_log_file_not_exists():
    with patch("src.api.owner_ops.Path.exists", return_value=False):
        result = stream_log(user={"username": "owner"})
        assert result == {"logs": ["Log file not yet created."]}


def test_stream_log_success():
    mock_lines = [f"Line {i}\n" for i in range(100)]
    with patch("src.api.owner_ops.Path.exists", return_value=True):
        with patch(
            "src.api.owner_ops.Path.open", mock_open(read_data="".join(mock_lines))
        ):
            result = stream_log(user={"username": "owner"})
            assert "logs" in result
            assert len(result["logs"]) == 50
            assert result["logs"][-1] == "Line 99\n"
            assert result["logs"][0] == "Line 50\n"


def test_stream_log_read_error():
    with patch("src.api.owner_ops.Path.exists", return_value=True):
        # Mocking open to raise an exception
        with patch(
            "src.api.owner_ops.Path.open", side_effect=Exception("Simulated read error")
        ):
            result = stream_log(user={"username": "owner"})
            assert "logs" in result
            assert len(result["logs"]) == 1
            assert result["logs"][0] == "Error reading log file: Simulated read error"
