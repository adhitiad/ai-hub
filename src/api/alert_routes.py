from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from src.api.auth import get_current_user
from src.core.database import alerts_collection, fix_id

router = APIRouter(prefix="/alerts", tags=["Alerts System"])


class AlertModel(BaseModel):
    symbol: str
    type: str  # 'PRICE' atau 'FORMULA'
    condition: str  # Untuk Price: 'ABOVE', 'BELOW'. Untuk Formula: 'RSI < 30', dll.
    target_price: float = 0.0  # Hanya untuk tipe PRICE
    note: str = ""


@router.post("/create")
async def create_alert(alert: AlertModel, user: dict = Depends(get_current_user)):
    new_alert = alert.dict()
    new_alert["user_id"] = str(user["_id"])
    new_alert["user_email"] = user["email"]
    new_alert["status"] = "ACTIVE"
    new_alert["created_at"] = datetime.utcnow()

    # Validasi Formula Sederhana (Security)
    if alert.type == "FORMULA":
        allowed_keywords = [
            "RSI",
            "MACD",
            "CLOSE",
            "OPEN",
            "VOLUME",
            "SMA",
            ">",
            "<",
            "AND",
            "OR",
            "==",
        ]
        if not any(k in alert.condition.upper() for k in allowed_keywords):
            raise HTTPException(400, "Formula tidak valid atau tidak didukung.")

    await alerts_collection.insert_one(new_alert)
    return {"status": "success", "message": "Alert created"}


@router.get("/list")
async def get_my_alerts(user: dict = Depends(get_current_user)):
    cursor = alerts_collection.find({"user_id": str(user["_id"])})
    alerts = await cursor.to_list(length=100)
    return [fix_id(a) for a in alerts]
