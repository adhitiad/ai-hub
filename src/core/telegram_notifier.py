import asyncio
import os

import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from src.core.database import users_collection
from src.core.logger import logger
from src.core.redis_client import redis_client

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


class TelegramNotifier:
    def __init__(self):
        self.base_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

    def _send_message_sync(self, chat_id, text):
        """
        Fungsi pengirim pesan via HTTP Request (Synchronous)
        """
        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",  # Biar bisa Bold/Italic
        }
        try:
            requests.post(url, json=payload, timeout=5)
        except Exception as e:
            logger.error(f"⚠️ Gagal kirim Telegram ke {chat_id}: {e}")

    async def broadcast_signal(self, signal_data):
        """
        🔥 FITUR UTAMA: Kirim sinyal ke SEMUA user di Database!
        """
        if not TELEGRAM_BOT_TOKEN:
            logger.warning("Telegram Token belum diset di .env!")
            return

        # 1. Format Pesan yang CATCHY & RAPI 🎨
        symbol = signal_data["Symbol"]
        action = signal_data["Action"]  # BUY / SELL
        price = signal_data["Price"]
        tp = signal_data["Tp"]
        sl = signal_data["Sl"]

        emoji_action = "🟢" if action == "BUY" else "🔴"

        message = (
            f"<b>{emoji_action} NEW SIGNAL: {symbol}</b>\n\n"
            f"🚀 <b>Action:</b> {action}\n"
            f"💵 <b>Price:</b> {price}\n\n"
            f"🎯 <b>TP:</b> {tp}\n"
            f"🛡️ <b>SL:</b> {sl}\n\n"
            f"🤖 <i>AI Confidence: {signal_data.get('Prob', 'N/A')}</i>\n"
            f"🐋 <i>Whale: {signal_data.get('Whale_Activity', '-')}</i>"
        )

        # 2. Ambil Semua User yang punya Telegram ID dari MongoDB
        # Kita filter hanya user yang punya field 'telegram_chat_id'
        cursor = users_collection.find(
            {"telegram_chat_id": {"$exists": True, "$ne": None}}
        )
        users = await cursor.to_list(length=5000)

        if not users:
            logger.info("📭 Tidak ada user Telegram yang terdaftar untuk dikirim.")
            return

        logger.info(f"📢 Broadcasting signal to {len(users)} users...")

        # 3. Kirim Paralel (Biar cepat & gak bikin server ngelag)
        tasks = []
        for user in users:
            chat_id = user["telegram_chat_id"]
            # Bungkus fungsi sync jadi async
            tasks.append(asyncio.to_thread(self._send_message_sync, chat_id, message))

        await asyncio.gather(*tasks)
        logger.info("✅ Broadcast selesai!")

    # Update src/core/telegram_notifier.py

    @staticmethod
    async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle command /start <kode>"""

        args = context.args
        if not args:
            await update.message.reply_text(
                "Halo! Gunakan kode dari website untuk binding. Contoh: /start A1B2C3"
            )
            return

        code = args[0]
        chat_id = update.effective_chat.id

        # 1. Cek Redis
        email = await redis_client.get(f"tg_bind:{code}")

        if not email:
            await update.message.reply_text("❌ Kode tidak valid atau kadaluarsa.")
            return

        # 2. Update Database User
        await users_collection.update_one(
            {"email": email},
            {"$set": {"telegram_chat_id": chat_id, "telegram_connected": True}},
        )

        # 3. Hapus Kode
        await redis_client.delete(f"tg_bind:{code}")

        await update.message.reply_text(
            f"✅ Sukses! Akun {email} terhubung. Notifikasi akan dikirim ke sini."
        )

    async def run_telegram_bot(self):
        """Jalankan sebagai Background Task di main.py"""
        if not TELEGRAM_TOKEN:
            return

        app = Application.builder().token(TELEGRAM_TOKEN).build()
        app.add_handler(CommandHandler("start", TelegramNotifier.start_handler))

        # Run polling
        await app.initialize()
        await app.start()
        await app.updater.start_polling()

    # Instance Global


telegram_bot = TelegramNotifier()
