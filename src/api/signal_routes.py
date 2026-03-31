from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import APIRouter, Depends, Query
from src.api.auth import get_current_user
from src.database.database import signals_collection, fix_id

router = APIRouter(prefix="/signals", tags=["Trading Signals"])

@router.get("/")
async def get_signals(
    status: str = Query("active", enum=["active", "expired"]),
    rank: Optional[str] = Query(None, enum=["ELITE", "PREMIUM", "SPECULATIVE"]),
    asset_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(10, enum=[5, 10, 25]),
    user: dict = Depends(get_current_user)
):
    skip = (page - 1) * limit
    now = datetime.now(timezone.utc)
    three_hours_ago = now - timedelta(hours=3)
    
    query = {}
    if status == "active":
        query["created_at"] = {"$gte": three_hours_ago}
    else:
        query["created_at"] = {"$lt": three_hours_ago}

    if rank:
        query["rank"] = rank
    
    if asset_type:
        query["asset_type"] = asset_type.upper()
    
    total = await signals_collection.count_documents(query)
    cursor = signals_collection.find(query).sort("created_at", -1).skip(skip).limit(limit)
    signals = await cursor.to_list(length=limit)
    
    return {
        "status": "success",
        "total": total,
        "page": page,
        "limit": limit,
        "data": [fix_id(s) for s in signals]
    }

@router.get("/stats")
async def get_signal_stats(user: dict = Depends(get_current_user)):
    cursor = signals_collection.find({"status": {"$in": ["WIN", "LOSS"]}})
    trades = await cursor.to_list(length=2000)
    
    if not trades:
        return {
            "win_rate": 0.0,
            "total_signals": 0,
            "wins": 0,
            "losses": 0
        }
    
    wins = len([t for t in trades if t["status"] == "WIN"])
    total = len(trades)
    win_rate = (wins / total) * 100 if total > 0 else 0
    
    return {
        "win_rate": round(win_rate, 2),
        "total_signals": total,
        "wins": wins,
        "losses": total - wins
    }
