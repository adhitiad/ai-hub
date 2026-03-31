import os
import shutil
import pytest
from unittest.mock import patch, MagicMock
import pandas as pd

from src.core.trainer import train_candidate, deploy_model, train_model_pipeline

@pytest.fixture
def mock_df_sufficient():
    # Create dummy DataFrame with at least 500 rows to simulate sufficient data
    return pd.DataFrame({'close': range(600), 'volume': range(600)})

@pytest.fixture
def mock_df_insufficient():
    # Create dummy DataFrame with less than 500 rows
    return pd.DataFrame({'close': range(100), 'volume': range(100)})

@patch("src.core.trainer.fetch_data")
@patch("src.core.trainer.TradingEnv")
@patch("src.core.trainer.PPO")
@patch("src.core.trainer.os.makedirs")
@patch("src.core.trainer.get_asset_info")
def test_train_candidate_success(mock_get_asset_info, mock_makedirs, mock_ppo, mock_env, mock_fetch_data, mock_df_sufficient):
    # Setup mocks
    mock_fetch_data.return_value = mock_df_sufficient
    mock_get_asset_info.return_value = {"category": "crypto"}

    mock_model_instance = MagicMock()
    mock_ppo.return_value = mock_model_instance

    # Execute
    result = train_candidate("BTCUSDT", total_timesteps=100)

    # Assert
    assert result["success"] is True
    assert "models/candidates/crypto/BTCUSDT.zip" in result["path"]

    mock_fetch_data.assert_called_once_with("BTCUSDT", period="2y", interval="1h")
    mock_env.assert_called_once()
    mock_ppo.assert_called_once()
    mock_model_instance.learn.assert_called_once_with(total_timesteps=100)
    mock_model_instance.save.assert_called_once()
    mock_makedirs.assert_called_once()

@patch("src.core.trainer.fetch_data")
def test_train_candidate_insufficient_data(mock_fetch_data, mock_df_insufficient):
    mock_fetch_data.return_value = mock_df_insufficient

    result = train_candidate("BTCUSDT")

    assert result["success"] is False
    assert result["error"] == "Data tidak cukup"

@patch("src.core.trainer.fetch_data")
def test_train_candidate_exception(mock_fetch_data):
    mock_fetch_data.side_effect = Exception("API Error")

    result = train_candidate("BTCUSDT")

    assert result["success"] is False
    assert "API Error" in result["error"]

@patch("src.core.trainer.os.path.exists")
@patch("src.core.trainer.os.makedirs")
@patch("src.core.trainer.shutil.copy")
@patch("src.core.trainer.get_asset_info")
def test_deploy_model_success(mock_get_asset_info, mock_copy, mock_makedirs, mock_exists):
    mock_get_asset_info.return_value = {"category": "crypto"}
    mock_exists.return_value = True

    result = deploy_model("BTCUSDT")

    assert result is True
    mock_exists.assert_called_once()
    mock_makedirs.assert_called_once()
    mock_copy.assert_called_once()

@patch("src.core.trainer.os.path.exists")
@patch("src.core.trainer.get_asset_info")
def test_deploy_model_failure_not_exists(mock_get_asset_info, mock_exists):
    mock_get_asset_info.return_value = {"category": "crypto"}
    mock_exists.return_value = False

    result = deploy_model("BTCUSDT")

    assert result is False
    mock_exists.assert_called_once()

@patch("src.core.trainer.train_candidate")
@patch("src.core.trainer.deploy_model")
def test_train_model_pipeline(mock_deploy, mock_train_candidate):
    mock_train_candidate.return_value = {"success": True, "path": "test.zip"}

    result = train_model_pipeline("BTCUSDT")

    assert result["success"] is True
    mock_train_candidate.assert_called_once()
    mock_deploy.assert_called_once_with("BTCUSDT")

@patch("src.core.trainer.train_candidate")
@patch("src.core.trainer.deploy_model")
def test_train_model_pipeline_failure(mock_deploy, mock_train_candidate):
    mock_train_candidate.return_value = {"success": False}

    result = train_model_pipeline("BTCUSDT")

    assert result["success"] is False
    mock_train_candidate.assert_called_once()
    mock_deploy.assert_not_called()


@patch("src.core.trainer.os.path.exists")
@patch("src.core.trainer.get_asset_info")
def test_deploy_model_exception(mock_get_asset_info, mock_exists):
    mock_get_asset_info.side_effect = Exception("Deploy Error")

    result = deploy_model("BTCUSDT")

    assert result is False
