import os
import time
import pytest
from unittest.mock import patch
from src.feature.continuous_learner import get_latest_model_path

@pytest.fixture
def mock_cwd(tmp_path):
    """Mocks os.getcwd() to return a temporary directory."""
    with patch("os.getcwd", return_value=str(tmp_path)):
        yield tmp_path

def test_get_latest_model_path_no_models_dir(mock_cwd):
    """Test when the 'models' directory does not exist."""
    result = get_latest_model_path("BTC", "crypto")
    assert result is None

def test_get_latest_model_path_empty_dir(mock_cwd):
    """Test when the 'models' directory exists but contains no models."""
    model_dir = mock_cwd / "models"
    model_dir.mkdir()

    result = get_latest_model_path("BTC", "crypto")
    assert result is None

def test_get_latest_model_path_no_matching_models(mock_cwd):
    """Test when the 'models' directory has files but none match the prefix."""
    model_dir = mock_cwd / "models"
    model_dir.mkdir()

    # Create non-matching file
    (model_dir / "ETH_crypto_v1.zip").touch()

    result = get_latest_model_path("BTC", "crypto")
    assert result is None

def test_get_latest_model_path_returns_latest(mock_cwd):
    """Test that the function returns the most recently created matching model."""
    model_dir = mock_cwd / "models"
    model_dir.mkdir()

    # Create matching models
    file1 = model_dir / "BTC_crypto_v1.zip"
    file1.touch()

    # Sleep to ensure file times are different (or use os.utime)
    # Using patch on getctime is safer to avoid time delays, but we can just use os.utime

    file2 = model_dir / "BTC_crypto_v2.zip"
    file2.touch()

    file3 = model_dir / "BTC_crypto_v3.zip"
    file3.touch()

    # Set explicitly older/newer access & modified times
    now = time.time()
    os.utime(file1, (now, now - 100))
    os.utime(file2, (now, now + 100)) # Most recently modified/created
    os.utime(file3, (now, now))

    # Actually, os.path.getctime on Linux is change time, on Windows creation time.
    # We can patch os.path.getctime to be deterministic.
    def mock_getctime(path):
        if "v1" in path: return 100
        if "v2" in path: return 300
        if "v3" in path: return 200
        return 0

    with patch("os.path.getctime", side_effect=mock_getctime):
        result = get_latest_model_path("BTC", "crypto")

    assert result == str(file2)
