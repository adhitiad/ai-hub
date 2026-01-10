import asyncio
import os
import sys

# Pastikan path project terbaca
sys.path.append(os.getcwd())

from src.core.data_loader import fetch_data_async
from src.core.database import assets_collection


async def clean_invalid_assets():
    print("🧹 Memulai Pembersihan Aset Invalid...")

    # 1. Ambil semua aset dari MongoDB
    all_assets = await assets_collection.find({}).to_list(None)
    total = len(all_assets)
    print(f"🔍 Total Aset di Database: {total}")

    deleted_count = 0
    valid_count = 0

    print("-" * 50)

    for i, asset in enumerate(all_assets):
        symbol = asset["symbol"]
        category = asset.get("category", "UNKNOWN")

        # Log progres
        print(f"[{i+1}/{total}] Checking {symbol}...", end=" ", flush=True)

        try:
            # 2. Coba Fetch Data (Gunakan limit kecil untuk cek eksistensi saja)
            # Kita set period='1mo' agar cepat
            df = await fetch_data_async(symbol, period="1mo", interval="1d")

            # 3. Logika Validasi
            if df.empty or len(df) < 5:
                # GAGAL / DATA KOSONG -> HAPUS
                await assets_collection.delete_one({"_id": asset["_id"]})
                print(f"❌ INVALID (No Data) -> DELETED")
                deleted_count += 1
            else:
                # SUKSES -> BIARKAN
                print(f"✅ VALID ({len(df)} candles)")
                valid_count += 1

        except Exception as e:
            # ERROR -> HAPUS (Asumsi simbol rusak)
            await assets_collection.delete_one({"_id": asset["_id"]})
            print(f"❌ ERROR ({str(e)}) -> DELETED")
            deleted_count += 1

    print("-" * 50)
    print(f"🎉 Selesai!")
    print(f"✅ Aset Valid Dipertahankan: {valid_count}")
    print(f"🗑️  Aset Invalid Dihapus    : {deleted_count}")


if __name__ == "__main__":
    # Pastikan library terinstall
    try:
        import ccxt
    except ImportError:
        print("⚠️ Library 'ccxt' belum terinstall. Install dulu: pip install ccxt")
        sys.exit(1)

    asyncio.run(clean_invalid_assets())
