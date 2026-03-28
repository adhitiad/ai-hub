# src/ml/model_monitoring.py
import warnings
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Dict, List

import numpy as np
from scipy import stats


@dataclass
class DriftReport:
    feature_name: str
    drift_detected: bool
    p_value: float
    statistic: float
    threshold: float


class ModelMonitor:
    def __init__(self, reference_data: np.ndarray, feature_names: List[str]):
        """
        reference_data: Data training/reference distribution
        feature_names: Nama feature sesuai urutan
        """
        self.reference_data = reference_data
        self.feature_names = feature_names
        self.reference_stats = self._compute_stats(reference_data)
        self.prediction_history = []
        self.performance_history = []

    def _compute_stats(self, data: np.ndarray) -> Dict:
        """Compute statistik reference"""
        return {
            "mean": np.mean(data, axis=0),
            "std": np.std(data, axis=0),
            "percentiles": np.percentile(data, [5, 25, 50, 75, 95], axis=0),
        }

    def detect_drift(
        self, current_data: np.ndarray, method: str = "ks_test", threshold: float = 0.05
    ) -> List[DriftReport]:
        """
        Deteksi drift antara reference dan current data
        """
        reports = []

        for i, feature in enumerate(self.feature_names):
            ref_feature = self.reference_data[:, i]
            curr_feature = current_data[:, i]

            if method == "ks_test":
                # Kolmogorov-Smirnov test
                statistic, p_value = stats.ks_2samp(ref_feature, curr_feature)
                drift_detected = p_value < threshold

            elif method == "psi":
                # Population Stability Index
                p_value, statistic = self._calculate_psi(ref_feature, curr_feature)
                drift_detected = statistic > 0.25  # PSI > 0.25 considered significant

            reports.append(
                DriftReport(
                    feature_name=feature,
                    drift_detected=drift_detected,
                    p_value=p_value,
                    statistic=statistic,
                    threshold=threshold,
                )
            )

        return reports

    def _calculate_psi(self, expected: np.ndarray, actual: np.ndarray) -> tuple:
        """Calculate Population Stability Index"""
        # Binning
        bins = np.percentile(expected, np.linspace(0, 100, 11))
        bins[0] = -np.inf
        bins[-1] = np.inf

        expected_percents = np.histogram(expected, bins=bins)[0] / len(expected)
        actual_percents = np.histogram(actual, bins=bins)[0] / len(actual)

        # Avoid division by zero
        expected_percents = np.where(expected_percents == 0, 0.0001, expected_percents)
        actual_percents = np.where(actual_percents == 0, 0.0001, actual_percents)

        psi = np.sum(
            (actual_percents - expected_percents)
            * np.log(actual_percents / expected_percents)
        )

        return 0, psi  # Return dummy p-value

    def track_prediction(self, prediction: Dict):
        """Track prediksi model"""
        self.prediction_history.append(
            {
                "timestamp": datetime.now(timezone.utc),
                "action": prediction["action"],
                "confidence": prediction["confidence"],
                "features": prediction.get("features"),
            }
        )

    def track_performance(self, trade_result: Dict):
        """Track performa actual trading"""
        self.performance_history.append(
            {
                "timestamp": datetime.now(timezone.utc),
                "symbol": trade_result["symbol"],
                "pnl": trade_result["pnl"],
                "predicted_action": trade_result["predicted_action"],
                "market_return": trade_result.get("market_return", 0),
            }
        )

    def get_performance_metrics(self, window_days: int = 30) -> Dict:
        """Get performance metrics untuk window tertentu"""
        cutoff = datetime.now(timezone.utc) - timedelta(days=window_days)
        recent_trades = [t for t in self.performance_history if t["timestamp"] > cutoff]

        if not recent_trades:
            return {}

        pnls = [t["pnl"] for t in recent_trades]
        returns = np.cumsum(pnls)

        # Calculate metrics
        total_return = sum(pnls)
        sharpe = self._calculate_sharpe(pnls)
        max_dd = self._calculate_max_drawdown(returns)
        win_rate = len([p for p in pnls if p > 0]) / len(pnls)

        return {
            "total_return": total_return,
            "sharpe_ratio": sharpe,
            "max_drawdown": max_dd,
            "win_rate": win_rate,
            "num_trades": len(recent_trades),
            "avg_trade": np.mean(pnls),
            "profit_factor": self._calculate_profit_factor(pnls),
        }

    def _calculate_sharpe(self, returns: List[float]) -> float:
        """Calculate Sharpe ratio"""
        if len(returns) < 2:
            return 0
        return np.mean(returns) / (np.std(returns) + 1e-8) * np.sqrt(252)

    def _calculate_max_drawdown(self, cumulative: np.ndarray) -> float:
        """Calculate maximum drawdown"""
        running_max = np.maximum.accumulate(cumulative)
        drawdown = (cumulative - running_max) / running_max
        return np.min(drawdown)

    def _calculate_profit_factor(self, returns: List[float]) -> float:
        """Calculate profit factor"""
        profits = sum([r for r in returns if r > 0])
        losses = abs(sum([r for r in returns if r < 0]))
        return profits / (losses + 1e-8)

    def should_retrain(
        self, min_sharpe: float = 1.0, min_win_rate: float = 0.5
    ) -> bool:
        """Determine if model needs retraining"""
        metrics = self.get_performance_metrics(window_days=30)

        if not metrics:
            return False

        # Check if performance degraded
        if metrics["sharpe_ratio"] < min_sharpe:
            return True

        if metrics["win_rate"] < min_win_rate:
            return True

        # Check for drift
        if len(self.prediction_history) > 100:
            recent_features = np.array(
                [p["features"] for p in self.prediction_history[-100:]]
            )
            drift_reports = self.detect_drift(recent_features)

            drifted_features = [r for r in drift_reports if r.drift_detected]
            if (
                len(drifted_features) > len(drift_reports) * 0.3
            ):  # >30% features drifted
                return True

        return False
