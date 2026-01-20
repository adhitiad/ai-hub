# src/core/explainer.py


def generate_explanation(symbol, technical_data, bandar_data):
    reasons = []

    # 1. Analisa Teknikal (Pattern)
    # Asumsi technical_data punya field 'pattern'
    if technical_data.get("pattern") == "BULLISH_ENGULFING":
        reasons.append(
            "Bullish Engulfing terdeteksi: Tanda pembalikan arah naik yang kuat."
        )

    if technical_data.get("rsi") < 30:
        reasons.append(
            f"RSI berada di {technical_data['rsi']} (Oversold): Harga sudah terlalu murah, potensi rebound."
        )

    # 2. Analisa Bandarmology
    if bandar_data.get("status") == "ACCUMULATION":
        reasons.append("Bandar Akumulasi: Pemain besar sedang membeli diam-diam.")

    if not reasons:
        return "AI merekomendasikan berdasarkan tren umum, namun tidak ada pola spesifik yang dominan."

    return "AI merekomendasikan posisi ini karena: " + "; ".join(reasons)
