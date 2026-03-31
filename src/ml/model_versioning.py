import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

import mlflow
from mlflow import pytorch

from src.core.logger import logger


@dataclass
class ModelMetadata:
    symbol: str
    model_type: str  # "PPO", "LSTM", "ENSEMBLE"
    metrics: Dict[str, float]
    params: Dict[str, Any]
    artifacts: Optional[List[str]] = None


class ModelVersioning:
    def __init__(self, tracking_uri="http://localhost:5000"):
        mlflow.set_tracking_uri(tracking_uri)
        mlflow.set_experiment("ai_trading_models")

    def log_model(
        self,
        model: Any,
        metadata: ModelMetadata,
    ):
        """Log model dengan versioning"""

        # Generate run name
        run_name = f"{metadata.symbol}_{metadata.model_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        with mlflow.start_run(run_name=run_name) as run:
            # Log parameters
            mlflow.log_params(
                {
                    "symbol": metadata.symbol,
                    "model_type": metadata.model_type,
                    "timesteps": metadata.params.get("timesteps"),
                    "learning_rate": metadata.params.get("learning_rate"),
                    "batch_size": metadata.params.get("batch_size"),
                    "architecture": json.dumps(metadata.params.get("architecture", {})),
                }
            )

            # Log metrics
            mlflow.log_metrics(
                {
                    "sharpe_ratio": metadata.metrics.get("sharpe_ratio", 0),
                    "win_rate": metadata.metrics.get("win_rate", 0),
                    "max_drawdown": metadata.metrics.get("max_drawdown", 0),
                    "total_return": metadata.metrics.get("total_return", 0),
                    "profit_factor": metadata.metrics.get("profit_factor", 0),
                }
            )

            # Log model
            pytorch.log_model(
                model,
                artifact_path="model",
                registered_model_name=f"trading_model_{metadata.symbol}",
            )

            # Log artifacts (confusion matrix, equity curve, dll)
            if metadata.artifacts:
                for artifact_path in metadata.artifacts:
                    if artifact_path:
                        mlflow.log_artifact(artifact_path)

            # Tagging
            mlflow.set_tags(
                {
                    "environment": (
                        "production"
                        if metadata.metrics.get("sharpe_ratio", 0) > 1.5
                        else "staging"
                    ),
                    "approved": (
                        "true"
                        if metadata.metrics.get("win_rate", 0) > 0.55
                        else "false"
                    ),
                    "symbol": metadata.symbol,
                }
            )

            run_id = run.info.run_id
            logger.info("✅ Model logged with run_id: %s", run_id)
            return run_id
