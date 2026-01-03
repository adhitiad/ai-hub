import math


def calculate_lot_size(balance, risk_percentage, sl_price, entry_price, asset_info):
    """
    Menghitung Lot Size yang aman secara dinamis.
    Mendukung Forex (Decimal Lot) dan Saham Indo (Integer Lot).
    """

    # 1. Tentukan Uang yang Siap Dirisikokan
    # Contoh: Saldo Rp 100 Juta, Risk 2% = Rp 2 Juta
    risk_amount = balance * (risk_percentage / 100)

    # Jarak SL (Perbedaan harga per unit/lembar)
    # Contoh BBCA: Entry 10.000, SL 9.500 -> Jarak 500 perak
    sl_distance = abs(entry_price - sl_price)

    if sl_distance == 0:
        return 0

    asset_type = asset_info.get("type", "forex")
    multiplier = asset_info.get("lot_multiplier", 100000)  # Default Forex Standard

    final_lot = 0

    # --- LOGIC SAHAM INDO (IDX) ---
    if asset_type == "stock_indo":
        # Rumus: Lot = Risk / (JarakSL * 100 lembar)
        # Contoh: 2 Juta / (500 perak * 100) = 2 Juta / 50.000 = 40 Lot

        risk_per_lot = sl_distance * multiplier  # Risk per 1 lot (100 lembar)

        if risk_per_lot == 0:
            return 0

        raw_lot = risk_amount / risk_per_lot

        # Saham Indo WAJIB Integer (kebawah)
        final_lot = math.floor(raw_lot)

        # Minimal beli 1 lot
        if final_lot < 1:
            final_lot = 0

    # --- LOGIC FOREX ---
    elif asset_type == "forex":
        # Rumus standar forex (approximate $10/pip untuk standard lot)
        # Kita gunakan pendekatan risk value real
        # Value per Lot = Multiplier * Price_Change

        risk_per_lot_unit = sl_distance * multiplier
        # Note: Untuk pair XXXUSD, ini akurat. Untuk Cross pair butuh konversi rate.
        # Kita simplifikasi asumsi akun USD.

        raw_lot = risk_amount / risk_per_lot_unit
        final_lot = round(raw_lot, 2)  # 2 Desimal (0.01)
        if final_lot < 0.01:
            final_lot = 0.01

    # --- LOGIC US STOCK ---
    else:
        # Bisa beli satuan (1 lembar)
        raw_qty = risk_amount / sl_distance
        final_lot = math.floor(raw_qty)  # Beli per lembar

    return final_lot
