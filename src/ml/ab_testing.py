# src/ml/ab_testing.py
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List

import numpy as np

from src.ml.model_registry import ModelRegistry


@dataclass
class Variant:
    model_version: str
    model_path: str
    traffic_percentage: float
    cumulative_reward: float = 0
    pulls: int = 0

    @property
    def avg_reward(self):
        return self.cumulative_reward / max(self.pulls, 1)


class ThompsonSamplingABTest:
    """
    Thompson Sampling untuk A/B testing model trading
    Menggunakan Beta distribution untuk Bayesian update
    """

    def __init__(self, variants: List[Variant]):
        self.variants = {v.model_version: v for v in variants}
        self.alpha = {v.model_version: 1 for v in variants}  # Successes + 1
        self.beta = {v.model_version: 1 for v in variants}  # Failures + 1

    def select_variant(self) -> Variant:
        """Select model berdasarkan Thompson Sampling"""
        samples = {}
        for version in self.variants:
            # Sample dari Beta distribution
            samples[version] = np.random.beta(self.alpha[version], self.beta[version])

        # Pilih variant dengan sample tertinggi
        best_version = max(samples.items(), key=lambda x: x[1])[0]
        return self.variants[best_version]

    def update_reward(self, version: str, reward: float):
        """Update hasil trading"""
        variant = self.variants[version]
        variant.pulls += 1
        variant.cumulative_reward += reward

        # Update Beta parameters (binary: profit=1, loss=0)
        if reward > 0:
            self.alpha[version] += 1
        else:
            self.beta[version] += 1

    def get_stats(self) -> Dict:
        """Get statistik A/B test"""
        return {
            version: {
                "traffic_pct": v.traffic_percentage,
                "pulls": v.pulls,
                "avg_reward": v.avg_reward,
                "alpha": self.alpha[version],
                "beta": self.beta[version],
                "confidence": (self.alpha[version] - 1)
                / (self.alpha[version] + self.beta[version] - 2),
            }
            for version, v in self.variants.items()
        }


# Implementasi dalam API
class ABTestManager:
    def __init__(self):
        self.active_tests: Dict[str, ThompsonSamplingABTest] = {}
        self.registry = ModelRegistry()

    def start_test(self, symbol: str, variants: List[Variant]):
        """Mulai A/B test untuk symbol"""
        self.active_tests[symbol] = ThompsonSamplingABTest(variants)
        print(f"🧪 A/B test started for {symbol} with {len(variants)} variants")

    def log_ab_assignment(self, user_id: str, symbol: str, model_version: str):
        """Log A/B test assignment to track user-model pairs"""
        # Simple logging implementation - can be extended to use a database
        print(
            f"📊 AB Test Assignment: User {user_id} -> Symbol {symbol} -> Model {model_version}"
        )

    def get_model_for_signal(self, symbol: str, user_id: str):
        """Get model berdasarkan A/B test assignment"""
        if symbol not in self.active_tests:
            # Return production model
            return self.get_production_model(symbol)

        ab_test = self.active_tests[symbol]
        variant = ab_test.select_variant()

        # Log assignment
        self.log_ab_assignment(user_id, symbol, variant.model_version)

        return variant

    def record_trade_result(self, symbol: str, version: str, pnl: float):
        """Record hasil trade untuk update A/B test"""
        if symbol in self.active_tests:
            # Normalize reward: profit=1, loss=0
            reward = 1 if pnl > 0 else 0
            self.active_tests[symbol].update_reward(version, reward)

    def should_promote(self, symbol: str, min_confidence: float = 0.95) -> bool:
        """Cek apakah model baru cukup bagus untuk dipromote"""
        if symbol not in self.active_tests:
            return False

        stats = self.active_tests[symbol].get_stats()

        # Cek confidence model baru vs baseline
        versions = list(stats.keys())
        if len(versions) < 2:
            return False

        new_model = versions[1]  # Asumsikan v1 adalah model baru
        baseline = versions[0]

        confidence_new = stats[new_model]["confidence"]
        confidence_baseline = stats[baseline]["confidence"]

        # Promote jika confidence new model > threshold dan lebih baik dari baseline
        if confidence_new > min_confidence and confidence_new > confidence_baseline:
            return True

        return False

    def get_production_model(self, symbol: str):
        """Get production model for symbol from registry"""
        return self.registry.get_production_model(symbol)


# Penggunaan dalam trading
ab_manager = ABTestManager()
