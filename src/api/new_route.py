from fastapi import APIRouter, Depends

from src.api.auth import get_current_user
from src.core.news_radar import news_radar

router = APIRouter(prefix="/news", tags=["News Radar"])


@router.get("/calendar")
def get_economic_calendar(user: dict = Depends(get_current_user)):
    """
    Mengambil jadwal berita ekonomi high-impact.
    """
    events = news_radar.get_upcoming_events(limit=7)
    return {"status": "success", "data": events}
