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
    if not isinstance(signal_data, dict):
        return "Sinyal tidak valid."

    action = signal_data.get("Action", "WAIT")
    symbol = signal_data.get("Symbol", "UNKNOWN")
    price = signal_data.get("Price", "N/A")
    tp = signal_data.get("Tp", "N/A")
    sl = signal_data.get("Sl", "N/A")
    ai_analysis = signal_data.get("AI_Analysis", "Technical Signal")

    # Icon berdasarkan action
    if action == "BUY":
        icon = "🟢"
    elif action == "SELL":
        icon = "🔴"
    else:
        icon = "⚪"

    msg = (
        f"<b>{icon} NEW SIGNAL: {symbol}</b>\n\n"
        f"<b>Action:</b> {action}\n"
        f"<b>Price:</b> {price}\n"
        f"<b>TP:</b> {tp}\n"
        f"<b>SL:</b> {sl}\n"
    )

    if "Confidence" in signal_data:
        msg += f"<b>Confidence:</b> {signal_data['Confidence']}\n"

    if "Timestamp" in signal_data:
        msg += f"<b>Time:</b> {signal_data['Timestamp']}\n"

    msg += (
        f"\n"
        f"📊 <b>Analysis:</b>\n"
        f"{ai_analysis}\n\n"
        f"<i>Disclaimer On. Do Your Own Research.</i>"
    )
    return msg
