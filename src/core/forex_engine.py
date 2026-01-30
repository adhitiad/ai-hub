class ForexEngine:
    def analyze_strength(self, pair: str):
        """
        Currency Strength Meter (CSM) Logic.
        Misal Pair: EURUSD. Kita cek kekuatan EUR vs USD.
        """
        # Simulasi Skor Kekuatan Mata Uang (0-100)
        import random

        base_currency = pair[:3]  # EUR
        quote_currency = pair[3:]  # USD

        strength_base = random.randint(0, 100)
        strength_quote = random.randint(0, 100)

        signal = "NEUTRAL"
        # Jika Base Kuat (80) & Quote Lemah (20) -> STRONG BUY
        if strength_base > 70 and strength_quote < 30:
            signal = "STRONG BUY"
        # Jika Base Lemah (20) & Quote Kuat (80) -> STRONG SELL
        elif strength_base < 30 and strength_quote > 70:
            signal = "STRONG SELL"

        return {
            "asset_type": "FOREX",
            "strength_meter": {
                base_currency: strength_base,
                quote_currency: strength_quote,
            },
            "signal": signal,
            "session": "LONDON_NEWYORK_OVERLAP",  # Hardcode simulasi
        }
