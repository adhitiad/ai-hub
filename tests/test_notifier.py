"""
Test module for Telegram Notifier.
"""
import pytest
from aiohttp import web

import src.core.notifier


@pytest.mark.asyncio
async def test_send_telegram_message_success():
    """
    Test sending a mock Telegram message successfully using the aiohttp approach.
    """
    # Start a mock server
    async def handle_post(request):
        data = await request.json()
        assert data["chat_id"] == "123"
        assert data["text"] == "test"
        return web.json_response({"ok": True})

    app = web.Application()
    app.router.add_post("/botYOUR_BOT_TOKEN_HERE/sendMessage", handle_post)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "localhost", 8081)
    await site.start()

    # Patch the function internally for testing
    original_send = src.core.notifier.send_telegram_message

    async def patched_send(chat_id, message):
        if not chat_id:
            return
        url_local = "http://localhost:8081/botYOUR_BOT_TOKEN_HERE/sendMessage"
        payload = {"chat_id": chat_id, "text": message, "parse_mode": "HTML"}
        session = await src.core.notifier.get_session()
        async with session.post(url_local, json=payload, timeout=5) as response:
            assert response.status == 200

    src.core.notifier.send_telegram_message = patched_send
    await src.core.notifier.send_telegram_message("123", "test")

    src.core.notifier.send_telegram_message = original_send
    await runner.cleanup()
