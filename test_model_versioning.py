#!/usr/bin/env python3
"""Test script for ModelVersioning class"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

try:
    from src.ml.model_versioning import ModelVersioning

    print("✅ SUCCESS: ModelVersioning imported successfully")

    # Check if pytorch is available
    from mlflow import pytorch

    print("✅ SUCCESS: pytorch imported from mlflow")

    # Create ModelVersioning instance
    versioning = ModelVersioning(tracking_uri="http://localhost:5000")
    print("✅ SUCCESS: ModelVersioning instance created")

    print("\n🎉 All imports and initialization successful!")

except ImportError as e:
    print(f"❌ Import Error: {e}")
except Exception as e:
    print(f"❌ Unexpected Error: {e}")
