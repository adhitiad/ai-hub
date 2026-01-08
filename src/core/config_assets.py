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
    """
    Mengambil konfigurasi aset.
    Jika tidak ada di dictionary ASSETS, gunakan logika fallback otomatis.
    """

    # 1. Cek Config Eksplisit (Hardcoded)
    for category, items in ASSETS.items():
        if symbol in items:
            info = items[symbol].copy()
            info["category"] = category
            return info

    # 2. Logika Fallback Dinamis (Auto-Detect)

    # --- A. SAHAM INDONESIA (*.JK) ---
    if symbol.endswith(".JK"):
        return {
            "type": "stock_indo",
            "category": "STOCKS_INDO",
            "pip_scale": 1,  # Pergerakan harga dalam Rupiah (fraksi harga)
            "lot_multiplier": 100,  # 1 Lot = 100 Lembar
        }

    # --- B. FOREX (*=X) ---
    if "=X" in symbol:
        # Deteksi pair JPY (Yen) karena pip scale-nya beda (2 desimal vs 4 desimal)
        is_jpy = "JPY" in symbol
        return {
            "type": "forex",
            "category": "FOREX",
            "pip_scale": 100 if is_jpy else 10000,
            "lot_multiplier": 100000,  # 1 Lot Standar = 100.000 Unit
        }

    # --- C. CRYPTO (-USD) ---

    return {
        "type": "crypto",
        "category": "CRYPTO",
        "pip_scale": 1,  # Tergantung harga, biasanya presisi tinggi
        "lot_multiplier": 1,
    }
