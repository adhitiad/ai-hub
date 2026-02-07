from datetime import datetime, timezone

from fastapi import APIRouter, Depends

from src.api.auth import get_current_user
from src.core.database import fix_id, signals_collection
from src.core.signal_bus import signal_bus

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/all")
async def get_dashboard_overview(user: dict = Depends(get_current_user)):
    signals = await signal_bus.get_all_signals()

    items = []
    counts = {"BUY": 0, "SELL": 0, "HOLD": 0, "OTHER": 0}

    for symbol, data in signals.items():
        action = str(data.get("Action", "HOLD")).upper()
        if action in counts:
            counts[action] += 1
        else:
            counts["OTHER"] += 1

        items.append({"symbol": symbol, **data})

    # Prioritize actionable signals first
    priority = {"BUY": 0, "SELL": 1, "HOLD": 2}
    items.sort(key=lambda x: priority.get(str(x.get("Action", "HOLD")).upper(), 3))

    open_cursor = (
        signals_collection.find({"status": "OPEN"}).sort("created_at", -1).limit(10)
    )
    open_trades = await open_cursor.to_list(length=10)

    return {
        "status": "ok",
        "server_time": datetime.now(timezone.utc),
        "signals": {
            "total": len(items),
            "counts": counts,
            "items": items[:50],
        },
        "open_trades": [fix_id(t) for t in open_trades],
    }
