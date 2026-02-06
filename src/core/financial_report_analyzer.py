import io
import json

from pypdf import PdfReader

from src.core.llm_analyst import LLMAnalyst
from src.core.logger import logger


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
            pages_to_read = min(len(reader.pages), max_pages)

            for i in range(pages_to_read):
                page = reader.pages[i]
                try:
                    if page and hasattr(page, "extract_text"):
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                except Exception as page_e:
                    logger.error(f"Error extracting text from page {i+1}: {page_e}")
                    continue

            return text
        except Exception as e:
            logger.error(f"PDF Extraction failed: {e}")
            import traceback

            logger.error(f"Extraction error traceback: {traceback.format_exc()}")
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
            # Menggunakan metode generate_response dari LLMAnalyst yang sudah di-refactor
            # is_json=True akan memaksa output JSON yang bersih
            response_str = await self.llm.generate_response(
                prompt=prompt,
                model="llama3-70b-8192",  # Model yang lebih kuat untuk analisis
                is_json=True,
            )

            if not response_str:
                raise Exception("LLM returned an empty response.")

            return json.loads(response_str)
        except json.JSONDecodeError as e:
            logger.error(f"LLM JSON Decode failed: {e}. Raw response: {{response_str}}")
            return {
                "error": "Gagal mem-parsing respons dari LLM",
                "raw_response": response_str,
            }
        except Exception as e:
            logger.error(f"LLM Analysis failed: {e}")
            return {"error": "Gagal menganalisis laporan", "detail": str(e)}
