from fastapi import APIRouter, Depends

# Fix Imports: Tambahkan 'src.' dan import 'fix_id'
from src.api.auth import get_current_user
from src.core.database import fix_id, users_collection

router = APIRouter(prefix="/user", tags=["User Data"])


@router.post("/watchlist/add")
async def add_watchlist(symbol: str, user: dict = Depends(get_current_user)):
    await users_collection.update_one(
        {"_id": user["_id"]}, {"$addToSet": {"watchlist": symbol}}
    )
    return {"status": "added", "symbol": symbol}


@router.delete("/watchlist/remove")
async def remove_watchlist(symbol: str, user: dict = Depends(get_current_user)):
    await users_collection.update_one(
        {"_id": user["_id"]}, {"$pull": {"watchlist": symbol}}
    )
    return {"status": "removed"}


@router.get("/watchlist")
async def get_my_watchlist(user: dict = Depends(get_current_user)):
    current_data = await users_collection.find_one({"_id": user["_id"]})
    return current_data.get("watchlist", []) if current_data else []


@router.get("/admin/search-user")
async def search_users(q: str):
    cursor = users_collection.find({"email": {"$regex": q, "$options": "i"}})
    users = await cursor.to_list(length=10)
    return [fix_id(u) for u in users]
