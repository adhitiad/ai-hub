# src/ml/model_versioning.py
import hashlib
import json
from datetime import datetime

import mlflow
from mlflow import pytorch

from src.core.logger import logger


class ModelVersioning:
    def __init__(self, tracking_uri="http://localhost:5000"):
        mlflow.set_tracking_uri(tracking_uri)
        mlflow.set_experiment("ai_trading_models")

    def log_model(
        self,
        model,
        symbol: str,
        model_type: str,  # "PPO", "LSTM", "ENSEMBLE"
        metrics: dict,
        params: dict,
        artifacts: list = [None],
    ):
        """Log model dengan versioning"""

        # Generate run name
        run_name = f"{symbol}_{model_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        with mlflow.start_run(run_name=run_name) as run:
            # Log parameters
            mlflow.log_params(
                {
                    "symbol": symbol,
                    "model_type": model_type,
                    "timesteps": params.get("timesteps"),
                    "learning_rate": params.get("learning_rate"),
                    "batch_size": params.get("batch_size"),
                    "architecture": json.dumps(params.get("architecture", {})),
                }
            )

            # Log metrics
            mlflow.log_metrics(
                {
                    "sharpe_ratio": metrics.get("sharpe_ratio", 0),
                    "win_rate": metrics.get("win_rate", 0),
                    "max_drawdown": metrics.get("max_drawdown", 0),
                    "total_return": metrics.get("total_return", 0),
                    "profit_factor": metrics.get("profit_factor", 0),
                }
            )

            # Log model
            pytorch.log_model(
                model,
                artifact_path="model",
                registered_model_name=f"trading_model_{symbol}",
            )

            # Log artifacts (confusion matrix, equity curve, dll)
            if artifacts:
                for artifact_path in artifacts:
                    mlflow.log_artifact(artifact_path)

            # Tagging
            mlflow.set_tags(
                {
                    "environment": (
                        "production"
                        if metrics.get("sharpe_ratio", 0) > 1.5
                        else "staging"
                    ),
                    "approved": (
                        "true" if metrics.get("win_rate", 0) > 0.55 else "false"
                    ),
                    "symbol": symbol,
                }
            )

            run_id = run.info.run_id
            logger.info("✅ Model logged with run_id: %s", run_id)
            return run_id
