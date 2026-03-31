# src/api/routes/monitoring.py
from fastapi import APIRouter, BackgroundTasks

from src.core.logger import logger
from src.core.pipeline import run_auto_optimization
from src.database.data_loader import fetch_data_async
from src.feature.feature_enginering import FEATURE_COLUMNS, get_model_input
from src.ml.feature_store_client import FeatureStoreClient
from src.ml.model_monitoring import ModelMonitor

router = APIRouter()


def get_recent_features(symbol: str):
    """Fetch recent features for a symbol"""
    feature_client = FeatureStoreClient()
    return feature_client.get_recent_features(symbol)


@router.get("/monitoring/model-health/{symbol}")
async def get_model_health(symbol: str, background_tasks: BackgroundTasks):
    """Get model health metrics"""
    # Create dummy reference data and feature names for the monitor
    # In production, this should be loaded from training data
    # Cek apakah perlu retrain

    reference = await fetch_data_async(
        symbol
    )  # in production, this should be loaded from a database

    reference_features = get_model_input(reference).values
    monitor = ModelMonitor(reference_features, FEATURE_COLUMNS)

    # Get recent features
    recent_features_df = get_recent_features(symbol)

    if recent_features_df.empty:
        return {
            "symbol": symbol,
            "performance": {},
            "drift_status": [],
            "recommendation": "no_data",
            "message": "No features available for model monitoring",
        }

    if monitor.should_retrain():
        logger.warning("⚠️ Model performance degraded. Triggering retraining...")
        background_tasks.add_task(run_auto_optimization, symbol)

    # Convert DataFrame to numpy array
    recent_features = recent_features_df.values

    return {
        "symbol": symbol,
        "performance": monitor.get_performance_metrics(window_days=30),
        "drift_status": [
            {
                "feature_name": r.feature_name,
                "drift_detected": r.drift_detected,
                "p_value": r.p_value,
                "statistic": r.statistic,
                "threshold": r.threshold,
            }
            for r in monitor.detect_drift(recent_features)
        ],
        "recommendation": "retrain" if monitor.should_retrain() else "healthy",
    }
