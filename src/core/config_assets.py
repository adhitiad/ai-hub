ASSETS = {
    # --- FOREX (Standard) ---
    "FOREX": {
        "EURUSD=X": {
            "type": "forex",
            "pip_scale": 10000,
            "lot_multiplier": 100000,
        },  # 1 Lot Std = 100k unit
        "JPY=X": {"type": "forex", "pip_scale": 100, "lot_multiplier": 100000},
        "GBPUSD=X": {"type": "forex", "pip_scale": 10000, "lot_multiplier": 100000},
        "AUDUSD=X": {"type": "forex", "pip_scale": 10000, "lot_multiplier": 100000},
    },
    # --- SAHAM INDONESIA (IDX) ---
    "STOCKS_INDO": {
        "BBCA.JK": {
            "type": "stock_indo",
            "pip_scale": 1,
            "lot_multiplier": 100,
        },  # 1 Lot = 100 Lembar
        "BBRI.JK": {"type": "stock_indo", "pip_scale": 1, "lot_multiplier": 100},
        "TLKM.JK": {"type": "stock_indo", "pip_scale": 1, "lot_multiplier": 100},
        "ASII.JK": {"type": "stock_indo", "pip_scale": 1, "lot_multiplier": 100},
        "GOTO.JK": {"type": "stock_indo", "pip_scale": 1, "lot_multiplier": 100},
    },
    # --- US STOCKS (Fractional allowed in some brokers) ---
    "STOCKS_US": {
        "AAPL": {
            "type": "stock_us",
            "pip_scale": 1,
            "lot_multiplier": 1,
        },  # 1 Unit = 1 Lembar
        "NVDA": {"type": "stock_us", "pip_scale": 1, "lot_multiplier": 1},
    },
}


def get_asset_info(symbol):
    # (Logika sama seperti sebelumnya)
    for category, items in ASSETS.items():
        if symbol in items:
            info = items[symbol]
            info["category"] = category
            return info
    return None
