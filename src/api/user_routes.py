from fastapi import APIRouter, Depends

from api.auth import get_current_user
from core.database import users_collection

router = APIRouter(prefix="/user", tags=["User Data"])


@router.post("/watchlist/add")
async def add_watchlist(symbol: str, user: dict = Depends(get_current_user)):
    # $addToSet mencegah duplikat otomatis
    await users_collection.update_one(
        {"_id": user["_id"]}, {"$addToSet": {"watchlist": symbol}}
    )
    return {"status": "added", "symbol": symbol}


@router.delete("/watchlist/remove")
async def remove_watchlist(symbol: str, user: dict = Depends(get_current_user)):
    # $pull menghapus item dari array
    await users_collection.update_one(
        {"_id": user["_id"]}, {"$pull": {"watchlist": symbol}}
    )
    return {"status": "removed"}


@router.get("/watchlist")
async def get_my_watchlist(user: dict = Depends(get_current_user)):
    # Ambil data terbaru dari DB (karena user session mungkin data lama)
    current_data = await users_collection.find_one({"_id": user["_id"]})
    return current_data.get("watchlist", [])


# Contoh: Admin mencari user berdasarkan email (Partial Search)
@router.get("/admin/search-user")
async def search_users(q: str):
    # Regex 'i' = case insensitive
    cursor = users_collection.find({"email": {"$regex": q, "$options": "i"}})
    users = await cursor.to_list(length=10)
    return [fix_id(u) for u in users]
