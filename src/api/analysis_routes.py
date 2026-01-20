import datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from src.api.auth import get_current_user
from src.core.database import db  # Asumsi ada collection 'reports'
from src.core.financial_report_analyzer import FinancialReportAnalyzer

router = APIRouter(prefix="/analysis", tags=["AI Financial Analysis"])
analyzer = FinancialReportAnalyzer()


@router.post("/upload-report")
async def analyze_financial_report(
    symbol: str = Form(...),
    period: str = Form(...),  # Contoh: "Q3 2024"
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user),
):
    # Validasi File
    if file.content_type != "application/pdf":
        raise HTTPException(400, "File harus PDF")

    content = await file.read()

    # Jalankan Analisis
    result = await analyzer.analyze_report(symbol, content)

    if "error" in result:
        raise HTTPException(500, result["error"])

    # Simpan Hasil ke DB agar bisa dilihat user lain
    report_doc = {
        "symbol": symbol.upper(),
        "period": period,
        "analysis": result,
        "uploaded_at": datetime.datetime.now(datetime.timezone.utc),
        "uploaded_by": user["email"],
    }
    # await db.reports.insert_one(report_doc)

    return result


@router.get("/latest/{symbol}")
async def get_latest_analysis(symbol: str):
    # Mock return (nanti ambil dari DB)
    return await db.reports.find_one({"symbol": symbol}, sort=[("uploaded_at", -1)])
