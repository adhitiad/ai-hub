from datetime import datetime, time
from unittest.mock import patch

import pytest
import pytz

from src.core.market_schedule import JAKARTA_TZ, is_market_open


class TestMarketSchedule:
    @patch("src.core.market_schedule.datetime")
    def test_is_market_open_forex_weekday(self, mock_datetime):
        """Test FOREX market open on weekday"""
        # Mock datetime for weekday (Monday), normal hours
        mock_now = mock_datetime.now.return_value
        mock_now.hour = 10
        mock_now.weekday.return_value = 0  # Monday

        result = is_market_open("FOREX")
        assert result is True

    @patch("src.core.market_schedule.datetime")
    def test_is_market_open_forex_weekend(self, mock_datetime):
        """Test FOREX market closed on weekend"""
        mock_now = mock_datetime.now.return_value
        mock_now.hour = 10
        mock_now.weekday.return_value = 5  # Saturday

        result = is_market_open("FOREX")
        assert result is False

    @patch("src.core.market_schedule.datetime")
    def test_is_market_open_forex_rollover_hours(self, mock_datetime):
        """Test FOREX market closed during rollover hours"""
        mock_now = mock_datetime.now.return_value
        mock_now.hour = 5  # Rollover hour
        mock_now.weekday.return_value = 0  # Monday

        result = is_market_open("FOREX")
        assert result is False

    @patch("src.core.market_schedule.datetime")
    def test_is_market_open_stocks_indo_weekday_session1(self, mock_datetime):
        """Test Indonesian stocks open during session 1"""
        mock_now = mock_datetime.now.return_value
        mock_now.weekday.return_value = 0  # Monday
        mock_now.time.return_value = time(10, 0)  # 10:00

        result = is_market_open("STOCKS_INDO")
        assert result is True

    @patch("src.core.market_schedule.datetime")
    def test_is_market_open_stocks_indo_friday_session2(self, mock_datetime):
        """Test Indonesian stocks open during Friday session 2"""
        mock_now = mock_datetime.now.return_value
        mock_now.weekday.return_value = 4  # Friday
        mock_now.time.return_value = time(15, 0)  # 15:00

        result = is_market_open("STOCKS_INDO")
        assert result is True

    @patch("src.core.market_schedule.datetime")
    def test_is_market_open_stocks_indo_weekend(self, mock_datetime):
        """Test Indonesian stocks closed on weekend"""
        mock_now = mock_datetime.now.return_value
        mock_now.weekday.return_value = 5  # Saturday
        mock_now.time.return_value = time(10, 0)

        result = is_market_open("STOCKS_INDO")
        assert result is False

    @patch("src.core.market_schedule.datetime")
    def test_is_market_open_stocks_indo_after_hours(self, mock_datetime):
        """Test Indonesian stocks closed after market hours"""
        mock_now = mock_datetime.now.return_value
        mock_now.weekday.return_value = 0  # Monday
        mock_now.time.return_value = time(16, 0)  # 16:00, after close

        result = is_market_open("STOCKS_INDO")
        assert result is False

    @patch("src.core.market_schedule.datetime")
    def test_is_market_open_pre_opening(self, mock_datetime):
        """Test Indonesian stocks open during pre-opening"""
        mock_now = mock_datetime.now.return_value
        mock_now.weekday.return_value = 0  # Monday
        mock_now.time.return_value = time(8, 50)  # 08:50, pre-opening

        result = is_market_open("STOCKS_INDO")
        assert result is True

    def test_is_market_open_other_assets(self):
        """Test other assets default to open"""
        result = is_market_open("CRYPTO")
        assert result is True

        result = is_market_open("US_STOCKS")
        assert result is True
