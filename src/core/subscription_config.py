from typing import Any, Dict, List, Optional


class SubscriptionConfig:
    PLANS = {
        "free": {
            "name": "Starter",
            "description": "Untuk pemula yang ingin memantau pasar.",
            "pricing": [],  # Gratis
            "daily_request_limit": 20,
            "ai_model": "Standard",
            "trial_benefit": {
                "minutes_per_month": 120,  # 2 Jam gratis per bulan
                "access_to": ["premium", "enterprise"],
            },
            "features": [
                "Data Saham IHSG (Delayed 15m)",
                "Screener Dasar (MA, RSI)",
                "1 Slot Portfolio",
                "Akses Komunitas Dasar",
            ],
            "excluded": [
                "Real-time Data",
                "AI Signals",
                "Bandarmology",
                "Crypto & Forex",
                "Risk Calculator",
            ],
        },
        "premium": {
            "name": "Pro Trader",
            "description": "Trader ritel aktif & karyawan yang butuh sinyal AI otomatis.",
            "pricing": [
                {"duration_months": 1, "price_idr": 144_999, "label": "1 Bulan"},
                {
                    "duration_months": 3,
                    "price_idr": 325_000,
                    "label": "3 Bulan (Hemat)",
                },
                {"duration_months": 6, "price_idr": 612_000, "label": "6 Bulan"},
                {
                    "duration_months": 12,
                    "price_idr": 1_175_000,
                    "label": "1 Tahun",
                    "bonus": "Gratis 1 Bulan Enterprise",
                },
            ],
            "daily_request_limit": 2000,
            "ai_model": "PPO Reinforcement Learning",
            "features": [
                "AI Signal (Buy/Sell Otomatis)",
                "Multi-Asset: Crypto (Whale Alert) & Forex",
                "Risk Calculator (Money Management)",
                "Telegram Bot (Notifikasi Pribadi)",
                "Bandarmology (Akumulasi Bandar)",
                "Real-time Data",
            ],
            "excluded": ["API Access", "Insider Hunter Graph", "Custom AI Request"],
        },
        "enterprise": {
            "name": "Institutional",
            "description": "Full-time trader, fund manager, & programmer.",
            "pricing": [
                {"duration_months": 3, "price_idr": 500_000, "label": "3 Bulan"},
                {"duration_months": 6, "price_idr": 800_000, "label": "6 Bulan"},
                {"duration_months": 12, "price_idr": 1_670_000, "label": "1 Tahun"},
            ],
            "daily_request_limit": 100_000,
            "ai_model": "Custom Fine-Tuned Model",
            "features": [
                "Semua Fitur Premium",
                "API Access (Untuk Bot Trading Sendiri)",
                "Insider Hunter (Grafik Relasi Konglomerasi)",
                "Custom Request (Training AI Sektor Khusus)",
                "Priority Server (Super Cepat)",
                "Akses Multi-User",
            ],
            "excluded": [],
        },
        "corporate": {
            "name": "Corporate",
            "description": "Solusi khusus untuk perusahaan sekuritas atau institusi besar.",
            "pricing": [
                {
                    "duration_months": 12,
                    "price_idr": 0,
                    "label": "Hubungi Kami",
                    "is_contact_required": True,
                }
            ],
            "daily_request_limit": 1_000_000,
            "ai_model": "Dedicated Server Model",
            "features": [
                "White-label Solution",
                "Dedicated Infrastructure",
                "Full Database Access",
                "24/7 Priority Support",
            ],
            "excluded": [],
        },
    }

    @staticmethod
    def get_plan(role: str) -> dict:
        return SubscriptionConfig.PLANS.get(role, SubscriptionConfig.PLANS["free"])


subscription_config = SubscriptionConfig()
