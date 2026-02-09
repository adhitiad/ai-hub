import math


class RiskCalculator:
    def __init__(self):
        pass

    def calculate_position_size(
        self,
        account_balance: float,
        entry_price: float,
        stop_loss_price: float,
        risk_percentage: float = 0.02,
    ) -> dict:
        """
        Menghitung ukuran posisi menggunakan metode Fixed Fractional Risk.

        Args:
            account_balance: Total uang user (Rp).
            entry_price: Harga beli saham.
            stop_loss_price: Harga cut loss.
            risk_percentage: Berapa % modal yang siap hilang per trade (Default 2%).

        Returns:
            Dict berisi jumlah lot dan estimasi kerugian.
        """
        if entry_price <= stop_loss_price:
            return {
                "error": "Entry price harus lebih besar dari Stop Loss (Long Position)"
            }

        # 1. Hitung Resiko per Saham (Rupiah)
        risk_per_share = entry_price - stop_loss_price

        # 2. Hitung Total Uang yang Siap Diresikokan (Rupiah)
        total_risk_capital = account_balance * risk_percentage

        # 3. Hitung Jumlah Lembar Saham
        number_of_shares = total_risk_capital / risk_per_share

        # 4. Konversi ke Lot (1 Lot = 100 Lembar di Indonesia)
        lots = math.floor(number_of_shares / 100)

        # 5. Hitung Modal yang dibutuhkan
        capital_required = lots * 100 * entry_price

        if capital_required > account_balance:
            # Jika modal kurang, sesuaikan lot maksimal modal
            lots = math.floor(account_balance / (entry_price * 100))
            note = "Dibatasi oleh saldo akun"
        else:
            note = "Sesuai manajemen risiko"

        return {
            "recommended_lots": int(lots),
            "entry_price": entry_price,
            "stop_loss": stop_loss_price,
            "risk_amount": f"Rp {total_risk_capital:,.0f}",
            "capital_required": f"Rp {capital_required:,.0f}",
            "note": note,
        }


# --- CONTOH PENGGUNAAN ---
# calculator = RiskCalculator()
# result = calculator.calculate_position_size(100_000_000, 5000, 4800, 0.02)
# print(result)
# Output: Beli 100 Lot. Jika kena SL, rugi 2 Juta (2% modal).# Output: Beli 100 Lot. Jika kena SL, rugi 2 Juta (2% modal).
