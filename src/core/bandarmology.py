import numpy as np
import pandas as pd
import pandas_ta as ta


class Bandarmology:
    """Kelas analisis Bandarmology untuk saham Indonesia"""

    def __init__(self):
        pass

    @staticmethod
    def analyze_bandar_flow(df):
        """
        Menganalisis pergerakan Smart Money (Bandar) berdasarkan Volume & Price Action.
        Tanpa kode broker, kita gunakan Volume Price Analysis (VPA).
        """

        # Pastikan data cukup
        if len(df) < 20:
            return {"status": "NEUTRAL", "score": 50, "message": "Data kurang"}

        # Ambil data terakhir
        last = df.iloc[-1]
        prev = df.iloc[-2]

        # 1. Hitung Rata-rata Volume 20 Hari
        vol_ma20 = df["Volume"].rolling(window=20).mean().iloc[-1]
        current_vol = last["Volume"]

        # 2. Hitung Perubahan Harga
        price_change = (last["Close"] - prev["Close"]) / prev["Close"] * 100  # Persen

        # 3. Hitung Volume Ratio (Seberapa besar ledakan volume hari ini)
        # Jika vol_ratio > 2.0 artinya Volume 2x lipat rata-rata (Ada Big Player masuk/keluar)
        vol_ratio = current_vol / vol_ma20 if vol_ma20 > 0 else 0

        # --- LOGIKA DETEKTOR BANDAR ---

        status = "NEUTRAL"
        score = 50  # 0 (Distribusi Parah) - 100 (Akumulasi Kuat)
        message = "Volume Normal"

        # KASUS A: MARK UP (Harga Naik + Volume Meledak)
        # Bandar sedang Hajar Kanan (HAKA)
        if price_change > 2.0 and vol_ratio > 1.5:
            status = "ACCUMULATION (MARK UP)"
            score = 85 + min(vol_ratio, 10)  # Max score naik jika volume makin besar
            message = "Big Player Hajar Kanan (Strong Buy)"

        # KASUS B: AKUMULASI SENYAP (Harga Sideways/Turun Dikit + Volume Besar)
        # Bandar nampung barang di bawah (Nampung panic selling ritel)
        elif -2.0 < price_change < 1.0 and vol_ratio > 1.5:
            status = "SILENT ACCUMULATION"
            score = 75
            message = "Bandar Nampung Barang (Siap-siap Naik)"

        # KASUS C: DISTRIBUSI (Harga Turun + Volume Besar)
        # Bandar Guyur Kiri (HAKI)
        elif price_change < -2.0 and vol_ratio > 1.5:
            status = "DISTRIBUTION (DUMP)"
            score = 20
            message = "Bandar Guyur Barang (Bahaya!)"

        # KASUS D: JEBAKAN BATMAN (Harga Naik + Volume Kecil)
        # Harga dinaikkan tanpa tenaga, biasanya pancingan
        elif price_change > 2.0 and vol_ratio < 0.7:
            status = "FAKE MOVE"
            score = 45
            message = "Kenaikan Tanpa Volume (Rawan Guyur)"

        # KASUS E: LOW LIQUIDITY (Saham Kuburan)
        elif vol_ratio < 0.2:
            status = "ILLIQUID"
            score = 10
            message = "Sepi Peminat / Saham Tidur"

        # --- TAMBAHAN: OBV (On Balance Volume) Trend ---
        # Jika OBV naik tapi harga flat -> Divergence Positif (Bandar Masuk)
        # Perlu perhitungan trend OBV 5 hari terakhir

        return {
            "status": status,
            "score": round(min(max(score, 0), 100)),  # Clamp 0-100
            "vol_ratio": round(vol_ratio, 2),
            "message": message,
        }


def analyze_bandar_flow(df):
    """Fungsi wrapper agar kompatibel dengan pemanggilan lama/test."""
    return Bandarmology.analyze_bandar_flow(df)
