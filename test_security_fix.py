
import asyncio
import pandas as pd
import unittest
from unittest.mock import MagicMock, AsyncMock
import watcher

class TestWatcherSecurityFix(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        # Mock alerts_collection
        self.original_alerts_collection = watcher.alerts_collection
        watcher.alerts_collection = MagicMock()
        watcher.alerts_collection.find = MagicMock()
        watcher.alerts_collection.update_one = AsyncMock()

    async def asyncTearDown(self):
        watcher.alerts_collection = self.original_alerts_collection

    async def test_check_alerts_safe_formula(self):
        symbol = "BTC/USDT"
        df = pd.DataFrame([{"Close": 51000, "Volume": 1000, "RSI_14": 25, "SMA_20": 50000}])

        # Valid alert that should trigger
        alert = {
            "_id": "alert1",
            "symbol": symbol,
            "type": "FORMULA",
            "condition": "CLOSE > 50000 AND RSI < 30",
            "status": "ACTIVE",
            "note": "Safe trigger"
        }

        watcher.alerts_collection.find.return_value.to_list = AsyncMock(return_value=[alert])

        await watcher.check_alerts(df, symbol)

        watcher.alerts_collection.update_one.assert_called_once()
        args, kwargs = watcher.alerts_collection.update_one.call_args
        self.assertEqual(args[0]["_id"], "alert1")
        self.assertEqual(kwargs["$set"]["status"], "TRIGGERED")

    async def test_check_alerts_malicious_formula(self):
        symbol = "BTC/USDT"
        df = pd.DataFrame([{"Close": 51000, "Volume": 1000, "RSI_14": 25, "SMA_20": 50000}])

        # Malicious alert attempting code execution
        alert = {
            "_id": "alert2",
            "symbol": symbol,
            "type": "FORMULA",
            "condition": "__import__('os').system('echo VULNERABLE')",
            "status": "ACTIVE",
            "note": "Malicious attempt"
        }

        watcher.alerts_collection.find.return_value.to_list = AsyncMock(return_value=[alert])

        # Should not raise exception, but also should not trigger (safe_eval returns False on error)
        await watcher.check_alerts(df, symbol)

        watcher.alerts_collection.update_one.assert_not_called()

    async def test_check_alerts_case_insensitivity(self):
        symbol = "BTC/USDT"
        df = pd.DataFrame([{"Close": 51000, "Volume": 1000, "RSI_14": 25, "SMA_20": 50000}])

        # Formula with lowercase variable names
        alert = {
            "_id": "alert3",
            "symbol": symbol,
            "type": "FORMULA",
            "condition": "close > 50000 and rsi < 30",
            "status": "ACTIVE",
            "note": "Lowercase trigger"
        }

        watcher.alerts_collection.find.return_value.to_list = AsyncMock(return_value=[alert])

        await watcher.check_alerts(df, symbol)

        watcher.alerts_collection.update_one.assert_called_once()

if __name__ == "__main__":
    unittest.main()
