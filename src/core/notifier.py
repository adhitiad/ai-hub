import asyncio

import requests

from src.core.logger import logger

# Config (Bisa dipindah ke .env)
TELEGRAM_BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"  # Dapat dari @BotFather


async def send_telegram_message(chat_id, message):
    """
    Mengirim pesan ke Telegram User.
    """
    if not chat_id:
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML",  # Agar bisa bold/italic
    }

    try:
        response = await asyncio.to_thread(requests.post, url, json=payload, timeout=5)
        if response.status_code != 200:
            logger.error("Telegram Fail: %s", response.text)
    except Exception as e:
        logger.error("Telegram Error: %s", e)


def format_signal_message(signal_data):
    """
    Format pesan sinyal agar cantik di HP.
    """
    # Icon berdasarkan action
    icon = "🟢" if signal_data["Action"] == "BUY" else "🔴"

    msg = (
        f"<b>{icon} NEW SIGNAL: {signal_data['Symbol']}</b>\n\n"
        f"<b>Action:</b> {signal_data['Action']}\n"
        f"<b>Price:</b> {signal_data['Price']}\n"
        f"<b>TP:</b> {signal_data['Tp']}\n"
        f"<b>SL:</b> {signal_data['Sl']}\n\n"
        f"📊 <b>Analysis:</b>\n"
        f"{signal_data.get('AI_Analysis', 'Technical Signal')}\n\n"
        f"<i>Disclaimer On. Do Your Own Research.</i>"
    )
    return msg
