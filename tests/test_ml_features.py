from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from src.core.ml_features import MarketMLAnalyzer


class TestMarketMLAnalyzer:
    def setup_method(self):
        """Setup before each test"""
        self.analyzer = MarketMLAnalyzer()

    def test_init(self):
        """Test initialization"""
        assert hasattr(self.analyzer, "scaler")
        assert hasattr(self.analyzer, "rf_model")

    def test_analyze_trend_slope(self):
        """Test trend slope analysis"""
        # Create sample data with upward trend
        dates = pd.date_range("2023-01-01", periods=30)
        prices = np.linspace(100, 110, 30)  # Linear increase
        df = pd.DataFrame({"Close": prices}, index=dates)

        slope = self.analyzer.analyze_trend_slope(df)
        assert slope > 0  # Should be positive

        # Test with insufficient data
        small_df = df.head(5)
        slope = self.analyzer.analyze_trend_slope(small_df)
        assert slope == 0.0

    def test_detect_market_regime(self):
        """Test market regime detection"""
        # Create sample data
        dates = pd.date_range("2023-01-01", periods=60)
        prices = np.random.normal(100, 2, 60)
        volumes = np.random.normal(1000, 100, 60)
        df = pd.DataFrame(
            {"Close": prices, "ATR_14": np.full(60, 1.0), "Volume": volumes},
            index=dates,
        )

        regime = self.analyzer.detect_market_regime(df)
        assert regime in [0, 1, 2]  # Valid regime values

        # Test with insufficient data
        small_df = df.head(10)
        regime = self.analyzer.detect_market_regime(small_df)
        assert regime == 1  # Default normal

    @patch("src.core.ml_features.joblib.load")
    def test_rf_signal_confirmation_with_model(self, mock_load):
        """Test RF signal confirmation with loaded model"""
        # Mock the RF model
        mock_model = MagicMock()
        mock_model.predict_proba.return_value = [[0.3, 0.7]]  # 70% win probability
        self.analyzer.rf_model = mock_model

        # Create sample data
        df = pd.DataFrame(
            {
                "Close": [100, 101, 102],
                "SMA_20": [99, 100, 101],
                "SMA_50": [98, 99, 100],
                "RSI_14": [50, 55, 60],
                "MACD_12_26_9": [0.1, 0.2, 0.3],
                "MACDh_12_26_9": [0.05, 0.1, 0.15],
                "ATR_14": [1.0, 1.1, 1.2],
                "Volume": [1000, 1100, 1200],
            }
        )

        score = self.analyzer.rf_signal_confirmation(df)
        assert isinstance(score, int)
        # With 70% prob, score should be positive
        assert score > 0

    def test_rf_signal_confirmation_no_model(self):
        """Test RF signal confirmation without model"""
        self.analyzer.rf_model = None

        df = pd.DataFrame({"Close": [100]})
        score = self.analyzer.rf_signal_confirmation(df)
        assert score == 0  # Neutral when no model

    def test_rf_signal_confirmation_with_nan(self):
        """Test RF signal confirmation with NaN values"""
        mock_model = MagicMock()
        self.analyzer.rf_model = mock_model

        df = pd.DataFrame(
            {
                "Close": [np.nan],
                "SMA_20": [100],
                "SMA_50": [100],
                "RSI_14": [50],
                "MACD_12_26_9": [0],
                "MACDh_12_26_9": [0],
                "ATR_14": [1],
                "Volume": [1000],
            }
        )

        score = self.analyzer.rf_signal_confirmation(df)
        assert score == 0  # Should return 0 for NaN input
