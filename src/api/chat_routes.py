import io
import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from pypdf import PdfReader

from src.api.auth import get_current_user
from src.core.llm_analyst import LLMAnalyst
from src.core.logger import logger
from src.core.news_radar import NewsRadar


class FinancialReportAnalyzer:
    def __init__(self):
        self.llm = LLMAnalyst()

    def extract_text_from_pdf(self, file_content: bytes, max_pages=5) -> str:
        """
        Ekstrak teks dari PDF. Kita batasi halaman karena LLM punya limit token.
        Biasanya ringkasan ada di 5 halaman pertama atau bagian 'Management Discussion'.
        """
        try:
            reader = PdfReader(io.BytesIO(file_content))
            text = ""
            # Ambil halaman awal (Summary) dan halaman Laporan Laba Rugi (biasanya di tengah/akhir)
            # Untuk simplifikasi, kita ambil N halaman pertama saja dulu
            pages_to_read = min(len(reader.pages), max_pages)

            for i in range(pages_to_read):
                text += reader.pages[i].extract_text() + "\n"

            return text
        except Exception as e:
            logger.error(f"PDF Extraction failed: {e}")
            return ""

    async def analyze_report(self, symbol: str, pdf_bytes: bytes):
        """Pipeline utama: PDF -> Text -> LLM -> JSON Summary"""

        # 1. Ekstrak Teks
        raw_text = self.extract_text_from_pdf(pdf_bytes)
        if not raw_text:
            return {"error": "Gagal membaca PDF"}

        # 2. Siapkan Prompt Spesifik
        prompt = f"""
        Anda adalah Analis Saham Senior. Tugas Anda adalah membaca potongan Laporan Keuangan {symbol} berikut dan berikan ringkasan padat.
        
        TEKS LAPORAN:
        {raw_text[:8000]}  # Potong agar tidak over token limit
        
        TUGAS:
        Analisis 3 aspek berikut dan berikan sentimen (POSITIVE/NEGATIVE/NEUTRAL):
        1. Profitabilitas (Revenue, Net Profit, Margin)
        2. Kesehatan Neraca (Utang, Kas)
        3. Prospek Manajemen (Kata kunci optimis/pesimis)

        OUTPUT FORMAT (WAJIB JSON):
        {{
            "overall_sentiment": "BULLISH" | "BEARISH" | "NEUTRAL",
            "score": 0-100,
            "highlights": [
                "Laba bersih naik XX% YoY...",
                "Utang jangka pendek meningkat..."
            ],
            "risk_factors": ["Harga komoditas turun...", "Kurs Rupiah melemah..."],
            "summary": "Satu paragraf kesimpulan..."
        }}
        """

        # 3. Tanya LLM
        try:
            # Asumsi LLMAnalyst punya method generate_json atau similar
            # Jika belum, kita pakai generate_response biasa lalu parse
            response = await self.llm.generate_response(prompt)

            # Simple cleaning jika LLM memberi markdown ```json ... ```

            if response is None:
                return {"error": "LLM returned empty response"}

            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]

            return json.loads(response)
        except Exception as e:
            logger.error(f"LLM Analysis failed: {e}")
            return {"error": "Gagal menganalisis laporan", "raw_response": str(e)}


router = APIRouter(prefix="/chat", tags=["AI Assistant"])


class ChatRequest(BaseModel):
    message: str
    symbol: Optional[str] = None  # Opsional, jika user bertanya spesifik saham


news = NewsRadar()
llm_analyst = LLMAnalyst()


@router.post("/ask")
async def ask_ai(req: ChatRequest, user: dict = Depends(get_current_user)):
    """
    RAG Logic:
    1. Ambil pertanyaan user.
    2. Jika ada simbol saham, ambil berita terkini (NewsRadar).
    3. Gabungkan Berita + Harga + Pertanyaan jadi Prompt.
    4. Kirim ke LLM.
    """
    context_data = ""

    # 1. Retrieval (Cari Berita/Data)
    if req.symbol:
        try:
            recent_news = await news.get_sentiment(req.symbol)
            context_data += f"\n[LATEST NEWS for {req.symbol}]: {recent_news}"
        except:

            pass

    # 2. Augmented Generation (Prompting)
    prompt = f"""
    You are a professional stock market analyst. 
    User Question: {req.message}
    
    Context Data:
    {context_data}
    
    Answer concisely based on the data provided. If you don't know, say so.
    """

    # 3. Generation (LLM)
    answer = await llm_analyst.generate_response(prompt)

    return {"answer": answer, "sources": req.symbol}
