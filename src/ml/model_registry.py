# src/ml/model_registry.py
from enum import Enum

import mlflow
from mlflow.tracking import MlflowClient

from src.core.logger import logger


class ModelStage(Enum):
    NONE = "None"
    STAGING = "Staging"
    PRODUCTION = "Production"
    ARCHIVED = "Archived"


class ModelRegistry:
    def __init__(self):
        self.client = MlflowClient()

    def register_model(self, run_id: str, model_name: str):
        """Register model ke registry"""
        model_version = mlflow.register_model(
            model_uri=f"runs:/{run_id}/model", name=model_name
        )
        logger.info(f"✅ Model registered: {model_name} v{model_version.version}")
        return model_version

    def transition_stage(
        self, model_name: str, version: int, stage: ModelStage, description: str = ""
    ):
        """Pindahkan model antar stage"""
        self.client.transition_model_version_stage(
            name=model_name,
            version=str(version),
            stage=stage.value,
            archive_existing_versions=(stage == ModelStage.PRODUCTION),
        )

        # Add description
        self.client.update_model_version(
            name=model_name, version=str(version), description=description
        )

        print(f"🔄 Model {model_name} v{version} moved to {stage.value}")

    def get_production_model(self, symbol: str):
        """Get model production untuk symbol tertentu"""
        model_name = f"trading_model_{symbol}"

        versions = self.client.get_latest_versions(
            name=model_name, stages=["Production"]
        )

        if versions:
            return versions[0]  # Return latest production version
        return None

    def compare_models(self, model_name: str, version1: int, version2: int):
        """Bandingkan dua versi model"""
        v1 = self.client.get_model_version(model_name, str(version1))
        v2 = self.client.get_model_version(model_name, str(version2))

        run1 = self.client.get_run(str(v1.run_id))
        run2 = self.client.get_run(str(v2.run_id))

        comparison = {
            "version_1": {"metrics": run1.data.metrics, "params": run1.data.params},
            "version_2": {"metrics": run2.data.metrics, "params": run2.data.params},
        }

        return comparison


# Penggunaan
registry = ModelRegistry()
