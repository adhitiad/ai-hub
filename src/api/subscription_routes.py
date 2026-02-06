from fastapi import APIRouter
from src.core.subscription_config import subscription_config

router = APIRouter(prefix="/subscription", tags=["Subscription"])


@router.get("/plans")
async def get_all_plans():
    """Mengembalikan daftar harga dan fitur untuk halaman Pricing"""
    return subscription_config.PLANS
