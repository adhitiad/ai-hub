from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from src.api.analysis_routes import router as analysis_router
from src.api.auth import get_current_user
from src.core.financial_report_analyzer import FinancialReportAnalyzer
from src.core.llm_analyst import LLMAnalyst


@pytest.fixture
def app():
    app = FastAPI()
    app.include_router(analysis_router)
    app.dependency_overrides[get_current_user] = lambda: {"email": "tester@example.com"}
    return app


@pytest_asyncio.fixture
async def client(app):
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


@pytest.mark.asyncio
async def test_upload_rejects_non_pdf(client):
    response = await client.post(
        "/analysis/upload-report",
        data={"symbol": "ABC", "period": "Q1 2025"},
        files={"file": ("report.txt", b"not a pdf", "text/plain")},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "File harus PDF"


@pytest.mark.asyncio
async def test_upload_saves_and_latest_returns(client):
    fake_result = {
        "overall_sentiment": "NEUTRAL",
        "score": 55,
        "highlights": ["Test highlight"],
        "risk_factors": ["Test risk"],
        "summary": "Test summary",
    }
    latest_doc = {"symbol": "ABC", "analysis": fake_result, "period": "Q1 2025"}

    with patch(
        "src.api.analysis_routes.analyzer.analyze_report",
        new=AsyncMock(return_value=fake_result),
    ), patch("src.api.analysis_routes.db") as mock_db:
        mock_db.reports.insert_one = AsyncMock()
        mock_db.reports.find_one = AsyncMock(return_value=latest_doc)

        response = await client.post(
            "/analysis/upload-report",
            data={"symbol": "abc", "period": "Q1 2025"},
            files={"file": ("report.pdf", b"%PDF-1.4", "application/pdf")},
        )

        assert response.status_code == 200
        assert response.json() == fake_result
        mock_db.reports.insert_one.assert_awaited_once()

        latest_response = await client.get("/analysis/latest/abc")
        assert latest_response.status_code == 200
        assert latest_response.json()["analysis"] == fake_result


@pytest.mark.asyncio
async def test_analyze_report_json_decode_error():
    analyzer = FinancialReportAnalyzer()

    with patch.object(
        analyzer, "extract_text_from_pdf", return_value="mock report text"
    ), patch.object(
        LLMAnalyst, "generate_response", new=AsyncMock(return_value="not json")
    ):
        result = await analyzer.analyze_report("ABC", b"%PDF-1.4")

    assert result["error"] == "Gagal mem-parsing respons dari LLM"
    assert result["raw_response"] == "not json"
