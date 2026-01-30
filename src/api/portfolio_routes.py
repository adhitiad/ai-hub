import asyncio
from datetime import datetime

import dotenv
from fastapi import APIRouter, Depends, HTTPException
from sympy import im

from src.api.auth import get_current_user
from src.core.database import users_collection

router = APIRouter(prefix="/portfolio", tags=["Portfolio Management"])


@router.post("/execute-virtual")
async def execute_virtual_order(
    symbol: str,
    action: str,
    qty: int,
    price: float,
    user: dict = Depends(get_current_user),
):
    """Simulasi Buy/Sell"""
    total_value = qty * price

    if action == "BUY":
        if user["virtual_balance"] < total_value:
            raise HTTPException(400, "Saldo virtual tidak cukup")

        # Kurangi saldo, Tambah Saham ke Portfolio
        await users_collection.update_one(
            {"email": user["email"]},
            {
                "$inc": {"virtual_balance": -total_value},
                "$push": {
                    "portfolio": {
                        "symbol": symbol,
                        "qty": qty,
                        "price": price,
                        "date": datetime.now(),
                    }
                },
            },
        )

    return {"status": "success", "msg": f"Virtual {action} {symbol} executed"}
