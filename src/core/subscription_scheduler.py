import asyncio
from datetime import datetime, timezone

from src.core.database import users_collection
from src.core.logger import logger

# # Mockup fungsi kirim notifikasi (Nanti diganti Email/WA Gateway)
# async def send_notification(user, days_left):
#     message = f"Halo {user['email']}, paket langganan Anda habis dalam {days_left} hari lagi. Segera perpanjang!"
#     logger.info(f"📨 SEND NOTIF to {user['email']}: {message}")
#     # Di sini panggil fungsi send_email() atau send_whatsapp()


def _ensure_utc(dt_value: datetime | None):
    if dt_value is None:
        return None
    if dt_value.tzinfo is None:
        return dt_value.replace(tzinfo=timezone.utc)
    return dt_value.astimezone(timezone.utc)


async def notify_expiring_users():
    """
    Mengirim notifikasi HANYA 1x sehari berdasarkan aturan:
    - 1 Minggu  (7 hari)  -> Notif H-3
    - 1 Bulan   (30 hari) -> Notif H-7 (1 Minggu)
    - 3 Bulan   (90 hari) -> Notif H-14 (2 Minggu)
    - 9 Bulan+  (Promo)   -> Notif H-30 (1 Bulan)
    """
    now = datetime.now(timezone.utc)
    today_str = now.strftime("%Y-%m-%d")

    logger.info("📩 Checking Expiry Notifications...")

    # Cari user aktif yang belum dinotifikasi HARI INI
    # (Mencegah spam jika scheduler jalan tiap jam)
    cursor = users_collection.find(
        {
            "subscription_status": "active",
            "plan_duration_days": {"$exists": True},  # Pastikan ada data durasi
            "last_expiry_notification": {"$ne": today_str},
        }
    )

    async for user in cursor:
        end_date = _ensure_utc(user.get("subscription_end_date"))
        if not end_date:
            continue

        # Hitung sisa hari
        delta = end_date - now
        days_left = delta.days

        # Ambil total durasi paket user (untuk nentuin aturan mana yg dipakai)
        total_duration = user.get("plan_duration_days", 30)

        should_notify = False

        # --- LOGIKA SESUAI PERMINTAAN ---

        # 1. Paket Mingguan (7 Hari) -> Notif H-3
        if total_duration <= 7:
            if days_left == 3:
                should_notify = True

        # 2. Paket Bulanan (30 Hari) -> Notif H-7 (1 Minggu)
        elif 7 < total_duration <= 31:
            if days_left == 7:
                should_notify = True

        # 3. Paket 3 Bulan (90 Hari) -> Notif H-14 (2 Minggu)
        elif 31 < total_duration <= 100:
            if days_left == 14:
                should_notify = True

        # 4. Paket Promo/Tahunan (> 9 Bulan) -> Notif H-30 (1 Bulan)
        elif total_duration > 100:
            if days_left == 30:
                should_notify = True

            # --- EKSEKUSI ---
            # if should_notify:
            #     await send_notification(user, days_left)

            # Tandai user sudah dikirimi notifikasi HARI INI
            await users_collection.update_one(
                {"_id": user["_id"]}, {"$set": {"last_expiry_notification": today_str}}
            )


async def send_message(user, message, msg_type="INFO"):
    """Fungsi dummy pengirim pesan (Email/WA)"""
    logger.info(f"📩 [{msg_type}] To {user['email']}: {message}")
    # Integration point: send_email(user['email'], message)


async def notify_status_updates():
    """
    Menangani notifikasi untuk:
    1. User yang SUDAH HABIS masa berlakunya (Expired).
    2. User FREE (Baru/Lama) untuk ditawari fitur Premium (Upselling).

    Aturan: 1 Hari Max 1x Kirim (Cek last_expiry_notification).
    """
    now = datetime.now(timezone.utc)
    today_str = now.strftime("%Y-%m-%d")

    # --- KASUS 1: MEMBERI TAHU MASA BERLANGGANAN SUDAH HABIS ---
    # Cari user yang status='expired' DAN belum dapat notif hari ini
    cursor_expired = users_collection.find(
        {
            "subscription_status": "expired",
            "last_expiry_notification": {"$ne": today_str},
        }
    )

    async for user in cursor_expired:
        msg = (
            f"Halo {user['email']}, Masa berlangganan Anda SUDAH HABIS per hari ini. "
            "Fitur Premium/Enterprise telah dinonaktifkan. "
            "Segera perpanjang langganan untuk akses kembali sinyal AI & Bandarmology!"
        )

        await send_message(user, msg, msg_type="EXPIRED")

        # Update Flag (Agar besok baru dikirim lagi, atau stop kirim logic lain)
        await users_collection.update_one(
            {"_id": user["_id"]}, {"$set": {"last_expiry_notification": today_str}}
        )

    # --- KASUS 2: PROMO KE USER BARU / FREE ---
    # Cari user role='free', BUKAN expired (murni free), dan belum dapat notif hari ini
    # Note: Kita batasi pengiriman promo ini agar tidak spamming (misal: tetap update flag harian)
    cursor_promo = users_collection.find(
        {
            "role": "free",
            "subscription_status": {"$ne": "expired"},  # User murni free/baru
            "last_expiry_notification": {"$ne": today_str},
        }
    )

    async for user in cursor_promo:
        # Cek tanggal pembuatan akun, jika baru daftar hari ini, kirim welcome message
        created_at = _ensure_utc(user.get("created_at"))
        is_new_user = False
        if created_at:
            if (now - created_at).days <= 1:
                is_new_user = True

        if is_new_user:
            msg = (
                f"Selamat Datang di AI Trading Hub, {user['email']}! "
                "Fitur kami meliputi: Sinyal AI Akurasi Tinggi, Detektor Bandar, & Analisa Paus Forex. "
                "Coba paket Premium mulai dari Rp 20rb/minggu!"
            )
        else:
            # User Free Lama (Reminder Berkala)
            msg = (
                f"Halo {user['email']}, mau profit lebih maksimal? "
                "Upgrade ke Enterprise untuk akses fitur 'God Mode' dan Sinyal Real-time tanpa delay. "
                "Cek menu Subscription sekarang."
            )

        await send_message(user, msg, msg_type="PROMO")

        # Update Flag Harian
        await users_collection.update_one(
            {"_id": user["_id"]}, {"$set": {"last_expiry_notification": today_str}}
        )


async def check_subscriptions():
    """
    Mengecek 2 hal:
    1. Apakah masa aktif bonus (Enterprise) sudah habis? -> Downgrade ke Premium.
    2. Apakah masa aktif langganan utama sudah habis? -> Downgrade ke Free.
    """
    now = datetime.now(timezone.utc)
    logger.info("⏳ Running Subscription Scheduler Check...")

    # --- 1. CEK BONUS EXPIRY (Enterprise -> Premium) ---
    # Cari user yang punya field 'bonus_end_date' < sekarang DAN masih role 'enterprise'
    bonus_expired_users = users_collection.find(
        {
            "bonus_end_date": {"$lt": now},
            "role": "enterprise",  # Asumsi bonusnya selalu enterprise
            "fallback_role": {"$exists": True},  # Pastikan ada role tujuannya
        }
    )

    async for user in bonus_expired_users:
        new_role = user.get("fallback_role", "premium")

        await users_collection.update_one(
            {"_id": user["_id"]},
            {
                "$set": {"role": new_role},
                "$unset": {
                    "bonus_end_date": "",
                    "fallback_role": "",
                },  # Hapus flag bonus
            },
        )
        logger.info(f"⬇️ BONUS ENDED: User {user['email']} downgraded to {new_role}")

    # --- 2. CEK SUBSCRIPTION EXPIRY (Premium/Ent -> Free) ---
    # Cari user yang subscription_end_date < sekarang DAN role bukan 'free'
    expired_subs = users_collection.find(
        {
            "subscription_end_date": {"$lt": now},
            "role": {"$ne": "free"},
            "subscription_status": "active",
        }
    )

    async for user in expired_subs:
        await users_collection.update_one(
            {"_id": user["_id"]},
            {
                "$set": {
                    "role": "free",
                    "subscription_status": "expired",
                    "daily_requests_limit": 50,  # Reset limit ke free
                }
            },
        )
        logger.info(f"🚫 SUBSCRIPTION EXPIRED: User {user['email']} set to FREE")


async def start_scheduler():
    """Looping setiap 1 jam sekali"""
    logger.info("⏰ Subscription Scheduler Started")
    while True:
        try:
            await check_subscriptions()
            await notify_expiring_users()
            await notify_status_updates()
        except Exception as e:
            logger.error(f"Scheduler Error: {e}")

        # Cek setiap 4 jam (14400 detik) agar tidak membebani server
        await asyncio.sleep(14400)
