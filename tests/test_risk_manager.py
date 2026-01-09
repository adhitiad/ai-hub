from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest

from src.core.risk_manager import check_circuit_breaker


class TestRiskManager:
    @pytest.mark.asyncio
    @patch("src.core.risk_manager.signals_collection")
    async def test_check_circuit_breaker_no_loss(self, mock_signals):
        """Test when no losses exceed limit"""
        # Mock signals collection - no LOSS signals
        mock_signals.find.return_value.to_list = AsyncMock(return_value=[])
        mock_signals.find.return_value.sort.return_value.limit.return_value.to_list = (
            AsyncMock(return_value=[])
        )

        result, reason = await check_circuit_breaker(100000)

        assert result is True
        assert reason == "OK"

    @pytest.mark.asyncio
    @patch("src.core.risk_manager.signals_collection")
    async def test_check_circuit_breaker_under_limit(self, mock_signals):
        """Test when losses are under the limit"""
        # Mock signals with some losses but under limit
        mock_signals.find.return_value.to_list = AsyncMock(
            return_value=[{"pnl_amount": -1000, "pips": 0, "lot_size_num": 0.1}]
        )
        mock_signals.find.return_value.sort.return_value.limit.return_value.to_list = (
            AsyncMock(return_value=[{"status": "LOSS"}])
        )

        result, reason = await check_circuit_breaker(100000)

        assert result is True

    @pytest.mark.asyncio
    @patch("src.core.risk_manager.signals_collection")
    async def test_check_circuit_breaker_over_limit(self, mock_signals):
        """Test when losses exceed the limit"""
        # Mock signals with losses over limit
        mock_signals.find.return_value.to_list = AsyncMock(
            return_value=[{"pnl_amount": -6000, "pips": 0, "lot_size_num": 0.1}]
        )
        mock_signals.find.return_value.sort.return_value.limit.return_value.to_list = (
            AsyncMock(return_value=[{"status": "LOSS"}])
        )

        result, reason = await check_circuit_breaker(100000)  # 5% = 5000

        assert result is False
        assert "CIRCUIT BREAKER TRIPPED" in reason

    @pytest.mark.asyncio
    @patch("src.core.risk_manager.signals_collection")
    async def test_check_circuit_breaker_consecutive_losses(self, mock_signals):
        """Test consecutive losses trigger"""
        mock_signals.find.return_value.to_list = AsyncMock(return_value=[])
        mock_signals.find.return_value.sort.return_value.limit.return_value.to_list = (
            AsyncMock(
                return_value=[
                    {"status": "LOSS"},
                    {"status": "LOSS"},
                    {"status": "LOSS"},
                    {"status": "LOSS"},
                    {"status": "LOSS"},
                    {"status": "WIN"},
                ]
            )
        )

        result, reason = await check_circuit_breaker(100000)

        assert result is False
        assert "Consecutive Losses" in reason
