class AnomalyDetector:
    """Deteksi Anomali pada Pergerakan Harga dan Sentimen Berita."""

    def detect_divergence(
        self, price_change_pct: float, sentiment_score: float
    ) -> dict:
        """
        price_change_pct: -5.0 sampai +5.0 (Persen)
        sentiment_score: -1.0 (Sangat Negatif) sampai +1.0 (Sangat Positif)
        """

        # 1. Kasus: Berita Sangat Bagus, Tapi Harga Jatuh (Distribution Alert)
        if sentiment_score > 0.5 and price_change_pct < -2.0:
            return {
                "status": "ANOMALY",
                "type": "DISTRIBUTION_DETECTED",
                "message": "Berita positif tapi harga dibuang. Waspada jebakan retail.",
                "severity": "HIGH",
            }

        # 2. Kasus: Berita Sangat Buruk, Tapi Harga Naik (Accumulation Alert)
        if sentiment_score < -0.5 and price_change_pct > 2.0:
            return {
                "status": "ANOMALY",
                "type": "ACCUMULATION_DETECTED",
                "message": "Berita negatif (FUD) tapi harga dijaga naik. Bandar sedang serok.",
                "severity": "MEDIUM",
            }

        return {"status": "NORMAL", "message": "Price action sesuai sentimen."}


# --- Integrasi Logic ---
# Logic ini dipanggil setelah `NewsCollector` selesai dan Market Close.
