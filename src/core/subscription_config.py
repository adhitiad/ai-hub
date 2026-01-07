from datetime import timedelta

# Konfigurasi Paket & Harga
SUBSCRIPTION_PLANS = {
    # --- MINGGUAN ---
    "PREMIUM_1W": {
        "name": "Premium Mingguan",
        "role": "premium",
        "price": 20999,
        "duration": timedelta(weeks=1),
        "description": "Akses Premium 7 Hari",
    },
    "ENTERPRISE_1W": {
        "name": "Enterprise Mingguan",
        "role": "enterprise",
        "price": 26999,
        "duration": timedelta(weeks=1),
        "description": "Akses Full Enterprise 7 Hari",
    },
    # --- BULANAN ---
    "PREMIUM_1M": {
        "name": "Premium Bulanan",
        "role": "premium",
        "price": 70000,
        "duration": timedelta(days=30),
        "description": "Akses Premium 30 Hari",
    },
    "ENTERPRISE_1M": {
        "name": "Enterprise Bulanan",
        "role": "enterprise",
        "price": 99999,
        "duration": timedelta(days=30),
        "description": "Akses Full Enterprise 30 Hari",
    },
    # --- 3 BULAN ---
    "PREMIUM_3M": {
        "name": "Premium Triwulan",
        "role": "premium",
        "price": 200000,
        "duration": timedelta(days=90),
        "description": "Hemat dengan paket 3 Bulan",
    },
    "ENTERPRISE_3M": {
        "name": "Enterprise Triwulan",
        "role": "enterprise",
        "price": 279999,
        "duration": timedelta(days=90),
        "description": "Hemat dengan paket 3 Bulan Enterprise",
    },
    # --- TAHUNAN (PROMO SPESIAL) ---
    "PREMIUM_PROMO": {
        "name": "Premium Tahunan Special",
        "role": "premium",
        "price": 1000000,
        "duration": timedelta(days=365),
        "has_bonus": True,
        "initial_role": "enterprise",  # Role yang didapat saat beli
        "bonus_duration": timedelta(days=30),  # Durasi role enterprise
        "fallback_role": "premium",  # Role setelah bonus habis
        "description": "Bayar 9 Bulan, Total 1 Tahun (Bonus 1 Bln Enterprise)",
    },
    "ENTERPRISE_PROMO": {
        "name": "Enterprise Tahunan Special",
        "role": "enterprise",
        "price": 1799000,
        "duration": timedelta(days=365),
        # Logic: 9 bulan bayar + 3 bulan gratis
        "description": "Bayar 9 Bulan, Gratis 3 Bulan (Total 1 Tahun)",
    },
}


def get_plan_details(plan_id: str):
    return SUBSCRIPTION_PLANS.get(plan_id)
