"""
Telegram Notifier module.
Handles sending asynchronous notifications to Telegram.
"""
import asyncio
import ssl

import aiohttp
import certifi

from src.core.logger import logger

# Config (Bisa dipindah ke .env)
TELEGRAM_BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"  # Dapat dari @BotFather


# Global aiohttp ClientSession
_SESSION = None

async def get_session() -> aiohttp.ClientSession:
    """
    Get or create a global aiohttp ClientSession.
    """
    global _SESSION # pylint: disable=global-statement
    if _SESSION is None or _SESSION.closed:
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        connector = aiohttp.TCPConnector(ssl=ssl_context)
        _SESSION = aiohttp.ClientSession(connector=connector)
    return _SESSION

async def close_session():
    """
    Close the global aiohttp ClientSession if it exists.
    """
    if _SESSION is not None and not _SESSION.closed:
        await _SESSION.close()

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
        session = await get_session()
        async with session.post(url, json=payload, timeout=5) as response:
            if response.status != 200:
                text = await response.text()
                logger.error("Telegram Fail: %s", text)
    except aiohttp.ClientError as e:
        logger.error("Telegram Error: %s", e)
    except asyncio.TimeoutError:
        logger.error("Telegram Error: Request timed out")
    except Exception as e: # pylint: disable=broad-exception-caught
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
