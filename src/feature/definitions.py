# feature_store/definitions.py
from datetime import timedelta

from feast import Entity, FeatureView, ValueType
from feast.field import Field
from feast.infra.offline_stores.file_source import FileSource
from feast.types import Float32, Int64, String

# Define entity
symbol_entity = Entity(
    name="symbol", value_type=ValueType.STRING, description="Trading symbol"
)

# Define data sources (using FileSource as placeholder - replace with actual sources like BigQuery/Redshift)
historical_data_source = FileSource(
    path="data/historical_data.parquet",
    event_timestamp_column="event_timestamp",
    created_timestamp_column="created_timestamp",
)

market_structure_source = FileSource(
    path="data/market_structure.parquet",
    event_timestamp_column="event_timestamp",
    created_timestamp_column="created_timestamp",
)

sentiment_source = FileSource(
    path="data/sentiment_data.parquet",
    event_timestamp_column="event_timestamp",
    created_timestamp_column="created_timestamp",
)

# Feature View untuk technical indicators
technical_indicators_fv = FeatureView(
    name="technical_indicators",
    entities=[symbol_entity],  # Now passing Entity object
    ttl=timedelta(hours=1),  # Features expire after 1 hour
    schema=[
        Field(name="rsi_14", dtype=Float32),
        Field(name="macd_line", dtype=Float32),
        Field(name="macd_signal", dtype=Float32),
        Field(name="bb_upper", dtype=Float32),
        Field(name="bb_middle", dtype=Float32),
        Field(name="bb_lower", dtype=Float32),
        Field(name="sma_20", dtype=Float32),
        Field(name="sma_50", dtype=Float32),
        Field(name="ema_12", dtype=Float32),
        Field(name="volume_sma_20", dtype=Float32),
        Field(name="atr_14", dtype=Float32),
    ],
    online=True,
    source=historical_data_source,  # Bisa dari BigQuery, Redshift, dll
)

# Feature View untuk market structure
market_structure_fv = FeatureView(
    name="market_structure",
    entities=[symbol_entity],  # Now passing Entity object
    ttl=timedelta(minutes=30),
    schema=[
        Field(name="support_level", dtype=Float32),
        Field(name="resistance_level", dtype=Float32),
        Field(name="trend_direction", dtype=String),
        Field(name="fvg_present", dtype=Int64),
        Field(name="liquidity_grab", dtype=Int64),
    ],
    online=True,
    source=market_structure_source,
)

# Feature View untuk sentiment
sentiment_fv = FeatureView(
    name="sentiment_features",
    entities=[symbol_entity],  # Now passing Entity object
    ttl=timedelta(minutes=15),
    schema=[
        Field(name="news_sentiment_score", dtype=Float32),
        Field(name="social_sentiment_score", dtype=Float32),
        Field(name="sentiment_momentum", dtype=Float32),
    ],
    online=True,
    source=sentiment_source,
)
