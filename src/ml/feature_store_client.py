# src/ml/feature_store_client.py
from datetime import datetime

import pandas as pd
from feast import FeatureStore

from src.core.logger import logger


class FeatureStoreClient:
    def __init__(self, repo_path: str = "feature_store"):
        self.store = FeatureStore(repo_path=repo_path)

    def get_online_features(self, symbol: str, feature_refs: list) -> pd.DataFrame:
        """Get real-time features untuk inference"""
        features = self.store.get_online_features(
            features=feature_refs, entity_rows=[{"symbol": symbol}]
        ).to_df()

        return features

    def get_historical_features(
        self,
        symbols: list,
        feature_refs: list,
        start_date: datetime,
        end_date: datetime,
    ) -> pd.DataFrame:
        """Get historical features untuk training"""
        entity_df = pd.DataFrame(
            {
                "symbol": symbols,
                "event_timestamp": pd.date_range(
                    start=start_date, end=end_date, periods=len(symbols)
                ),
            }
        )

        features = self.store.get_historical_features(
            entity_df=entity_df, features=feature_refs
        ).to_df()

        return features

    def store_features(self, symbol: str, df: pd.DataFrame):
        """Store features ke offline store dan materialize ke online store"""
        # Pastikan dataframe memiliki required columns: event_timestamp dan created_timestamp
        if "event_timestamp" not in df.columns:
            df["event_timestamp"] = pd.to_datetime(df.index)

        if "created_timestamp" not in df.columns:
            df["created_timestamp"] = pd.Timestamp.now()

        # Tambahkan symbol column jika tidak ada
        if "symbol" not in df.columns:
            df["symbol"] = symbol

        # Simpan ke offline store (Parquet file)
        df.to_parquet(f"data/{symbol}_features.parquet")
        logger.info("✅ Features saved to data/%s_features.parquet", symbol)

        # Materialize features ke online store (akan mengambil dari offline store)
        # Materialize features untuk waktu terbaru
        end_date = pd.Timestamp.now()
        start_date = end_date - pd.Timedelta(hours=1)
        self.materialize(start_date, end_date)

    def get_recent_features(self, symbol: str, limit: int = 100) -> pd.DataFrame:
        """Get recent features for a specific symbol"""
        # First, get all available feature views
        feature_refs = [
            "technical_indicators:rsi_14",
            "technical_indicators:macd_line",
            "technical_indicators:macd_signal",
            "technical_indicators:sma_20",
            "technical_indicators:sma_50",
            "market_structure:support_level",
            "market_structure:resistance_level",
            "market_structure:trend_direction",
            "sentiment_features:news_sentiment_score",
            "sentiment_features:social_sentiment_score",
        ]

        try:
            # Get online features
            features = self.store.get_online_features(
                features=feature_refs, entity_rows=[{"symbol": symbol}]
            ).to_df()

            return features
        except Exception as e:
            logger.error("Failed to get recent features for %s: %s", symbol, e)
            return pd.DataFrame()

    def materialize(self, start_date: datetime, end_date: datetime):
        """Materialize features dari offline ke online store"""
        self.store.materialize(start_date, end_date)
        logger.info("✅ Features materialized: %s to %s", start_date, end_date)


# Penggunaan dalam training
feature_client = FeatureStoreClient()
