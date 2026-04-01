import os
import shutil
import pytest
from unittest.mock import patch, MagicMock

from src.core.trainer import deploy_model, CANDIDATE_DIR, PRODUCTION_DIR

@patch("src.core.trainer.shutil.copy")
@patch("src.core.trainer.os.makedirs")
@patch("src.core.trainer.os.path.exists")
@patch("src.core.trainer.get_asset_info")
def test_deploy_model_success(mock_get_asset_info, mock_exists, mock_makedirs, mock_copy):
    """Test successful deployment of a model."""
    mock_get_asset_info.return_value = {"category": "crypto"}
    mock_exists.return_value = True

    symbol = "BTCUSDT"
    result = deploy_model(symbol)

    assert result is True

    expected_src = f"{CANDIDATE_DIR}/crypto/BTCUSDT.zip"
    expected_dst = f"{PRODUCTION_DIR}/crypto/BTCUSDT.zip"

    mock_exists.assert_called_once_with(expected_src)
    mock_makedirs.assert_called_once_with(os.path.dirname(expected_dst), exist_ok=True)
    mock_copy.assert_called_once_with(expected_src, expected_dst)

@patch("src.core.trainer.shutil.copy")
@patch("src.core.trainer.os.makedirs")
@patch("src.core.trainer.os.path.exists")
@patch("src.core.trainer.get_asset_info")
def test_deploy_model_source_not_found(mock_get_asset_info, mock_exists, mock_makedirs, mock_copy):
    """Test deployment when candidate model does not exist."""
    mock_get_asset_info.return_value = {"category": "crypto"}
    mock_exists.return_value = False

    symbol = "BTCUSDT"
    result = deploy_model(symbol)

    assert result is False

    expected_src = f"{CANDIDATE_DIR}/crypto/BTCUSDT.zip"

    mock_exists.assert_called_once_with(expected_src)
    mock_makedirs.assert_not_called()
    mock_copy.assert_not_called()

@patch("src.core.trainer.shutil.copy")
@patch("src.core.trainer.os.makedirs")
@patch("src.core.trainer.os.path.exists")
@patch("src.core.trainer.get_asset_info")
def test_deploy_model_no_category_info(mock_get_asset_info, mock_exists, mock_makedirs, mock_copy):
    """Test deployment when asset info has no category or is None."""
    mock_get_asset_info.return_value = None
    mock_exists.return_value = True

    symbol = "UNKNOWN_ASSET"
    result = deploy_model(symbol)

    assert result is True

    expected_src = f"{CANDIDATE_DIR}/common/UNKNOWN_ASSET.zip"
    expected_dst = f"{PRODUCTION_DIR}/common/UNKNOWN_ASSET.zip"

    mock_exists.assert_called_once_with(expected_src)
    mock_makedirs.assert_called_once_with(os.path.dirname(expected_dst), exist_ok=True)
    mock_copy.assert_called_once_with(expected_src, expected_dst)

@patch("src.core.trainer.shutil.copy")
@patch("src.core.trainer.os.makedirs")
@patch("src.core.trainer.os.path.exists")
@patch("src.core.trainer.get_asset_info")
def test_deploy_model_exception_handling(mock_get_asset_info, mock_exists, mock_makedirs, mock_copy):
    """Test exception handling during deployment."""
    mock_get_asset_info.return_value = {"category": "forex"}
    mock_exists.return_value = True
    mock_copy.side_effect = Exception("Disk full")

    symbol = "EURUSD"
    result = deploy_model(symbol)

    assert result is False

    expected_src = f"{CANDIDATE_DIR}/forex/EURUSD.zip"
    expected_dst = f"{PRODUCTION_DIR}/forex/EURUSD.zip"

    mock_exists.assert_called_once_with(expected_src)
    mock_makedirs.assert_called_once_with(os.path.dirname(expected_dst), exist_ok=True)
    mock_copy.assert_called_once_with(expected_src, expected_dst)

@patch("src.core.trainer.shutil.copy")
@patch("src.core.trainer.os.makedirs")
@patch("src.core.trainer.os.path.exists")
@patch("src.core.trainer.get_asset_info")
def test_deploy_model_symbol_sanitization(mock_get_asset_info, mock_exists, mock_makedirs, mock_copy):
    """Test that special characters in symbol are replaced."""
    mock_get_asset_info.return_value = {"category": "crypto"}
    mock_exists.return_value = True

    symbol = "BTC=USDT^"
    result = deploy_model(symbol)

    assert result is True

    # Notice = and ^ should be replaced with empty string
    expected_src = f"{CANDIDATE_DIR}/crypto/BTCUSDT.zip"
    expected_dst = f"{PRODUCTION_DIR}/crypto/BTCUSDT.zip"

    mock_exists.assert_called_once_with(expected_src)
    mock_makedirs.assert_called_once_with(os.path.dirname(expected_dst), exist_ok=True)
    mock_copy.assert_called_once_with(expected_src, expected_dst)
