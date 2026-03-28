from typing import Optional

from fastapi import APIRouter, Depends

from src.api.auth import get_current_user
from src.core.config_assets import ASSETS
from src.database.database import assets_collection

router = APIRouter(prefix="/assets", tags=["Assets"])


@router.get("/list")
async def list_assets(
    category: Optional[str] = None,
    user: dict = Depends(get_current_user),
):
    """
    Mengambil semua simbol aset dari database (MongoDB).
    Fallback ke config_assets.py jika database kosong.
    Query param `category` untuk filter: FOREX, STOCKS_INDO, STOCKS_US, CRYPTO
    """
    try:
        query = {}
        if category:
            query["category"] = category.upper()

        cursor = assets_collection.find(query, {"_id": 0}).sort("category", 1)
        assets = await cursor.to_list(length=500)

        # Jika database kosong, fallback ke config_assets.py
        if not assets:
            assets = _get_assets_from_config(category)

        return {"count": len(assets), "assets": assets}

    except Exception:
        # Jika MongoDB error, fallback ke config statis
        fallback = _get_assets_from_config(category)
        return {"count": len(fallback), "assets": fallback, "source": "config_fallback"}


def _get_assets_from_config(category: Optional[str] = None) -> list:
    """Konversi ASSETS dict dari config_assets.py ke format list yang sama dengan DB."""
    result = []
    for cat, items in ASSETS.items():
        if category and cat != category.upper():
            continue
        for symbol, info in items.items():
            result.append(
                {
                    "symbol": symbol,
                    "category": cat,
                    "type": info.get("type", "unknown"),
                    "pip_scale": info.get("pip_scale", 1),
                    "lot_multiplier": info.get("lot_multiplier", 1),
                }
            )
    return result
