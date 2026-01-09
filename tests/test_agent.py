from unittest.mock import AsyncMock, MagicMock, patch

import pandas as pd
import pytest

from src.core.agent import get_detailed_signal


# Sample Data Mock
@pytest.fixture
def sample_df():
    return pd.DataFrame(
        {
            "Close": [100.0, 101.0, 102.0],
            "High": [101.0, 102.0, 103.0],
            "Low": [99.0, 100.0, 101.0],
            "Open": [99.0, 100.0, 101.0],
            "Volume": [1000, 1500, 2000],
            "ATR_14": [1.0, 1.1, 1.2],
            "SMA_20": [98.0, 99.0, 100.0],
            "SMA_50": [95.0, 96.0, 97.0],
            "RSI_14": [55.0, 60.0, 65.0],
            "MACD_12_26_9": [0.5, 0.6, 0.7],
            "MACDh_12_26_9": [0.1, 0.2, 0.3],
        }
    )


@pytest.mark.asyncio
class TestAgent:

    @patch("src.core.agent.PPO")
    @patch("src.core.agent.fetch_data")
    @patch("src.core.agent.check_circuit_breaker", new_callable=AsyncMock)
    @patch("src.core.agent.check_correlation_risk", new_callable=AsyncMock)
    async def test_get_detailed_signal_hold_action(
        self, mock_corr, mock_circuit, mock_fetch, mock_ppo, sample_df
    ):
        """Test when PPO predicts HOLD"""
        # 1. Setup Mocks
        mock_circuit.return_value = (True, "OK")  # Circuit Breaker LOLOS
        mock_corr.return_value = (True, "OK")  # Correlation LOLOS
        mock_fetch.return_value = sample_df  # Data Fetch SUKSES

        # Mock Model PPO (Action 0 = HOLD)
        mock_model = MagicMock()
        mock_model.predict.return_value = (0, None)
        mock_ppo.load.return_value = mock_model

        with patch("glob.glob", return_value=["model.zip"]):
            result = await get_detailed_signal(
                "TEST", {"type": "forex", "category": "forex"}
            )

        # 2. Assertions
        assert result["Action"] == "HOLD"
        assert result["Symbol"] == "TEST"

    @patch("src.core.agent.PPO")
    @patch("src.core.agent.fetch_data")
    @patch("src.core.agent.check_circuit_breaker", new_callable=AsyncMock)
    @patch("src.core.agent.check_correlation_risk", new_callable=AsyncMock)
    @patch("src.core.agent.calculate_kelly_lot")  # Mock Kelly
    async def test_get_detailed_signal_buy_action(
        self, mock_kelly, mock_corr, mock_circuit, mock_fetch, mock_ppo, sample_df
    ):
        """Test when PPO predicts BUY"""
        # 1. Setup Mocks
        mock_circuit.return_value = (True, "OK")
        mock_corr.return_value = (True, "OK")
        mock_fetch.return_value = sample_df

        # Mock Kelly Lot
        mock_kelly.return_value = (0.1, "Kelly 5%")

        # Mock Model PPO (Action 1 = BUY)
        mock_model = MagicMock()
        mock_model.predict.return_value = (1, None)
        mock_ppo.load.return_value = mock_model

        with patch("glob.glob", return_value=["model.zip"]):
            result = await get_detailed_signal(
                "TEST", {"type": "forex", "category": "forex"}
            )

        # 2. Assertions
        assert "BUY" in result["Action"]
        assert result["LotNum"] == 0.1
        assert "Kelly" in result["AI_Analysis"]

    @patch("src.core.agent.check_circuit_breaker", new_callable=AsyncMock)
    async def test_get_detailed_signal_circuit_breaker_reject(self, mock_circuit):
        """Test Circuit Breaker Rejection (Return False)"""
        # Setup Mock: Circuit Breaker TRIPPED
        mock_circuit.return_value = (False, "Daily Loss Limit Hit")

        result = await get_detailed_signal("TEST", {"type": "forex"})

        # Assertion: Agent harus return False (bukan Dict)
        assert result is False

    @patch("src.core.agent.check_circuit_breaker", new_callable=AsyncMock)
    @patch("src.core.agent.check_correlation_risk", new_callable=AsyncMock)
    async def test_get_detailed_signal_correlation_reject(
        self, mock_corr, mock_circuit
    ):
        """Test Correlation Rejection (Return False)"""
        mock_circuit.return_value = (True, "OK")
        # Setup Mock: Correlation RISK
        mock_corr.return_value = (False, "Too much exposure in USD")

        result = await get_detailed_signal("TEST", {"type": "forex"})

        # Assertion: Agent harus return False
        assert result is False

    @patch("src.core.agent.fetch_data")
    @patch("src.core.agent.check_circuit_breaker", new_callable=AsyncMock)
    @patch("src.core.agent.check_correlation_risk", new_callable=AsyncMock)
    async def test_get_detailed_signal_empty_data(
        self, mock_corr, mock_circuit, mock_fetch
    ):
        """Test Empty Data Handling"""
        mock_circuit.return_value = (True, "OK")
        mock_corr.return_value = (True, "OK")
        # Setup Mock: Data Kosong
        mock_fetch.return_value = pd.DataFrame()

        with patch("glob.glob", return_value=["model.zip"]):
            result = await get_detailed_signal(
                "TEST", {"type": "forex", "category": "forex"}
            )

        # Assertion: Harus return HOLD dengan alasan No Data
        assert result["Action"] == "HOLD"
        assert "No Data" in result["Reason"]

    @patch("src.core.agent.check_circuit_breaker", new_callable=AsyncMock)
    async def test_get_detailed_signal_invalid_asset(self, mock_circuit):
        """Test Invalid Asset Config"""
        # Test dengan config kosong
        result = await get_detailed_signal("TEST", None)

        # Assertion: Harus return Error Dict
        assert "error" in result
        assert "Asset not config" in result["error"]

    @patch("src.core.agent.PPO")
    @patch("src.core.agent.fetch_data")
    @patch("src.core.agent.check_circuit_breaker", new_callable=AsyncMock)
    @patch("src.core.agent.check_correlation_risk", new_callable=AsyncMock)
    async def test_get_detailed_signal_no_model(
        self, mock_corr, mock_circuit, mock_fetch, mock_ppo
    ):
        """Test No Model Found"""
        mock_circuit.return_value = (True, "OK")
        mock_corr.return_value = (True, "OK")

        # Setup Mock: Glob return empty list (Model tidak ditemukan)
        with patch("glob.glob", return_value=[]):
            result = await get_detailed_signal(
                "TEST", {"type": "forex", "category": "forex"}
            )

        # Assertion: Harus HOLD
        assert result["Action"] == "HOLD"
        assert "No Model" in result["Reason"]
