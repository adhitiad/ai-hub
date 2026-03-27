import asyncio
import os

import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from src.core.logger import logger

# PERBAIKAN: Import dari src.database.database yang benar
from src.database.database import users_collection
from src.database.redis_client import redis_client

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


class TelegramNotifier:
    def __init__(self):
        self.base_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

    def _send_message_sync(self, chat_id, text):
        url = f"{self.base_url}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
        }
        try:
            requests.post(url, json=payload, timeout=5)
        except Exception as e:
            logger.error("⚠️ Gagal kirim Telegram ke %s: %s", chat_id, e)

    async def broadcast_signal(self, signal_data):
        if not TELEGRAM_BOT_TOKEN:
            logger.warning("Telegram Token belum diset di .env!")
            return

        symbol = signal_data.get("Symbol", "UNKNOWN")
        action = signal_data.get("Action", "HOLD")
        price = signal_data.get("Price", 0)
        tp = signal_data.get("Tp", 0)
        sl = signal_data.get("Sl", 0)

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

        # Hanya kirim ke user premium/enterprise yang punya TG & berstatus aktif
        cursor = users_collection.find(
            {
                "telegram_chat_id": {"$exists": True, "$ne": None},
                "role": {"$in": ["premium", "enterprise"]},
                "subscription_status": "active",
            }
        )
        users = await cursor.to_list(length=5000)

        if not users:
            logger.info("📭 Tidak ada user Telegram aktif yang dituju.")
            return

        logger.info(
            "📢 Broadcasting signal %s to %d Telegram users...", symbol, len(users)
        )

        tasks = [
            asyncio.to_thread(
                self._send_message_sync, user["telegram_chat_id"], message
            )
            for user in users
        ]
        await asyncio.gather(*tasks)
        logger.info("✅ Telegram Broadcast untuk %s selesai!", symbol)

    @staticmethod
    async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
        args = context.args
        if not args:
            if update.message:
                await update.message.reply_text(
                    "Halo! Gunakan kode dari website untuk binding. Contoh: /start A1B2C3"
                )
            return

        code = args[0]
        if not update.effective_chat:
            return
        chat_id = update.effective_chat.id

        email = await redis_client.get(f"tg_bind:{code}")

        if not email:
            if update.message:
                await update.message.reply_text("❌ Kode tidak valid atau kadaluarsa.")
            return

        await users_collection.update_one(
            {"email": email},
            {"$set": {"telegram_chat_id": chat_id, "telegram_connected": True}},
        )

        await redis_client.delete(f"tg_bind:{code}")

        if update.message:
            await update.message.reply_text(
                f"✅ Sukses! Akun {email} terhubung. Notifikasi premium akan dikirim ke sini."
            )

    async def run_telegram_bot(self):
        if not TELEGRAM_BOT_TOKEN:
            return

        app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        app.add_handler(CommandHandler("start", TelegramNotifier.start_handler))

        await app.initialize()
        await app.start()
        if app.updater:
            await app.updater.start_polling()


telegram_bot = TelegramNotifier()
