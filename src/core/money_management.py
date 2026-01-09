import math

from src.core.database import assets_collection, signals_collection, users_collection
from src.core.logger import logger


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


async def check_correlation_risk(new_symbol):
    """
    Cek apakah kita sudah punya posisi di aset yang 'mirip' (satu grup).
    """
    # Cari posisi yang sedang OPEN
    cursor = signals_collection.find({"status": "OPEN"})
    active_positions = await cursor.to_list(length=100)

    active_symbols = [p["symbol"] for p in active_positions]

    # Cek Grup
    # Fetch all assets to determine groups
    all_assets_cursor = assets_collection.find({})
    all_assets = await all_assets_cursor.to_list(length=None)  # Fetch all assets

    # Group assets by category
    categories = {}
    for asset in all_assets:
        category = asset.get("category", "UNKNOWN")
        categories.setdefault(category, []).append(asset["symbol"])

    for group_name, members in categories.items():
        if (
            new_symbol in members and group_name != "UNKNOWN"
        ):  # Only check for known categories
            exposure_count = sum(
                1 for s in active_symbols if s in members
            )  # Count active positions in this group
            if exposure_count >= 2:  # Limit Max 2 positions per sector/group
                logger.warning(
                    f"Correlation Risk: Too much exposure in {group_name} for {new_symbol}"
                )
                return False, f"Risk: Too much exposure in {group_name}"
    return True, "OK"


def calculate_kelly_lot(balance, win_rate_prob, risk_reward_ratio, sl_pips, asset_info):
    """
    Menghitung Lot Size menggunakan KELLY CRITERION.
    Rumus Kelly: K% = W - [(1 - W) / R]
    W = Win Probability (0.0 - 1.0)
    R = Win/Loss Ratio (Reward:Risk)
    """
    # Safety: Kelly murni terlalu agresif, kita pakai 'Half Kelly' atau 'Quarter Kelly'
    # agar tidak bangkrut (Ruin Risk).

    # 1. Hitung Kelly Fraction
    if risk_reward_ratio == 0:
        risk_reward_ratio = 1

    k_percent = win_rate_prob - ((1 - win_rate_prob) / risk_reward_ratio)

    # Jika Kelly negatif (jangan trade), atau batasi max 5% per trade (Quarter Kelly konservatif)
    k_percent = max(0, min(k_percent, 0.05))  # Capped at 5% risk

    if k_percent <= 0:
        return 0, "Kelly says NO TRADE"

    # 2. Konversi % Risiko ke Nominal Uang
    risk_amount = balance * k_percent

    # 3. Konversi Nominal ke Lot Size (Sama seperti fungsi lama)
    multiplier = asset_info.get("lot_multiplier", 100000)
    asset_type = asset_info.get("type", "forex")

    # Jarak SL dalam harga (bukan pips)
    # Asumsi sl_pips parameter disini sudah dikonversi ke selisih harga (price diff)
    # Jika parameter sl_pips adalah pip murni (misal 50 pip), konversi dulu:
    # price_diff = sl_pips * scale

    # Sederhananya, kita pakai logika lama calculate_lot_size tapi risk_amount-nya dari Kelly

    # ... (Logic konversi ke Lot sama seperti sebelumnya) ...
    # Saya tulis ulang simplified-nya:

    sl_distance = sl_pips  # Asumsi input sudah dalam selisih harga
    if sl_distance == 0:
        return 0, "SL Zero"

    final_lot = 0
    if asset_type == "stock_indo":
        risk_per_lot = sl_distance * multiplier
        if risk_per_lot > 0:
            final_lot = math.floor(risk_amount / risk_per_lot)
    else:  # Forex
        risk_per_lot_unit = sl_distance * multiplier
        if risk_per_lot_unit > 0:
            final_lot = round(risk_amount / risk_per_lot_unit, 2)
            if final_lot < 0.01:
                final_lot = 0.01

    return final_lot, f"Kelly {k_percent*100:.1f}%"


# Fungsi Wrapper agar kompatibel dengan kode lama
async def get_safe_lot_size(
    symbol, balance, sl_price, entry_price, asset_info, ai_confidence
):
    """
    Fungsi Utama yang menggabungkan Korelasi & Kelly.
    """
    # 1. Cek Korelasi (Markowitz Simplifikasi)
    is_safe, msg = await check_correlation_risk(symbol)
    if not is_safe:
        return 0, msg  # Reject Trade

    # 2. Hitung RR Ratio & SL Distance
    sl_dist = abs(entry_price - sl_price)
    if sl_dist == 0:
        return 0, "SL Error"

    # Estimasi TP (Asumsi 1:2 default jika tidak ada info TP, tapi di agent.py kita punya TP)
    # Kita anggap rasio 1:2 sebagai baseline konservatif untuk rumus Kelly
    risk_reward = 2.0

    # Win Rate dari AI (0-100 -> 0.0-1.0)
    win_prob = ai_confidence / 100.0

    # 3. Hitung Kelly
    lot, note = calculate_kelly_lot(balance, win_prob, risk_reward, sl_dist, asset_info)

    return lot, note
