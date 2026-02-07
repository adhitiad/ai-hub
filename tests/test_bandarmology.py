import numpy as np
import pandas as pd
import pytest

from src.core.bandarmology import analyze_bandar_flow


class TestBandarmology:
    def test_analyze_bandar_flow_accumulation(self):
        """Test accumulation detection"""
        # Create data that should trigger accumulation
        dates = pd.date_range("2023-01-01", periods=25)
        df = pd.DataFrame(
            {
                "Close": [100] * 24 + [102],  # Price up 2%
                "Volume": [1000] * 20 + [2000] * 5,  # Volume spike in last 5 days
                "High": [101] * 25,
                "Low": [99] * 25,
                "Open": [100] * 25,
            },
            index=dates,
        )

        # Add required columns for MA calculation
        df["SMA_20"] = df["Close"].rolling(20).mean()
        df["SMA_50"] = df["Close"].rolling(50).mean()

        result = analyze_bandar_flow(df)

        assert "status" in result
        assert "score" in result
        assert "message" in result
        assert result["score"] >= 0

    def test_analyze_bandar_flow_distribution(self):
        """Test distribution detection"""
        dates = pd.date_range("2023-01-01", periods=25)
        df = pd.DataFrame(
            {
                "Close": [102] * 24 + [99],  # Price down > 2%
                "Volume": [1000] * 20 + [2000] * 5,  # Volume spike
                "High": [103] * 25,
                "Low": [98] * 25,
                "Open": [102] * 25,
            },
            index=dates,
        )

        df["SMA_20"] = df["Close"].rolling(20).mean()
        df["SMA_50"] = df["Close"].rolling(50).mean()

        result = analyze_bandar_flow(df)

        assert "status" in result
        assert result["score"] <= 50  # Distribution should have lower score

    def test_analyze_bandar_flow_insufficient_data(self):
        """Test with insufficient data"""
        dates = pd.date_range("2023-01-01", periods=10)
        df = pd.DataFrame(
            {
                "Close": [100] * 10,
                "Volume": [1000] * 10,
                "High": [101] * 10,
                "Low": [99] * 10,
                "Open": [100] * 10,
            },
            index=dates,
        )

        result = analyze_bandar_flow(df)

        assert result["status"] == "NEUTRAL"
        assert result["score"] == 50

    def test_analyze_bandar_flow_fake_move(self):
        """Test fake move detection (high price, low volume)"""
        dates = pd.date_range("2023-01-01", periods=25)
        df = pd.DataFrame(
            {
                "Close": [100] * 24 + [103],  # Price up > 2%
                "Volume": [1000] * 24 + [500],  # Low volume
                "High": [104] * 25,
                "Low": [101] * 25,
                "Open": [100] * 25,
            },
            index=dates,
        )

        df["SMA_20"] = df["Close"].rolling(20).mean()
        df["SMA_50"] = df["Close"].rolling(50).mean()

        result = analyze_bandar_flow(df)

        assert result["score"] < 50  # Fake move should have lower score
