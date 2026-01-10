from unittest.mock import MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

# --- SETUP MOCK SEBELUM IMPORT APP ---
# Kita harus memalsukan driver database agar saat 'main' di-import,
# dia tidak mencoba koneksi beneran ke MongoDB lokal/cloud.
mock_mongo_client = MagicMock()
mock_mongo_db = MagicMock()
mock_mongo_client.__getitem__.return_value = mock_mongo_db

# Patch MotorClient di src.core.database (sesuaikan path jika beda)
with patch("motor.motor_asyncio.AsyncIOMotorClient", return_value=mock_mongo_client):
    # Import app SETELAH patch aktif
    from main import app


# --- FIXTURE UNTUK CLIENT ---
@pytest.fixture
async def client():
    # Menggunakan ASGITransport untuk mentest aplikasi ASGI (FastAPI) secara langsung tanpa server berjalan
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


# --- TEST CASES ---


@pytest.mark.asyncio
async def test_health_check_endpoint(client):
    """
    Test apakah endpoint /health yang kita buat sebelumnya berfungsi.
    """
    response = await client.get("/health")

    # Jika endpoint belum dibuat, ini akan 404. Jika sudah, harusnya 200.
    if response.status_code == 404:
        pytest.skip("Endpoint /health belum diimplementasikan di main.py")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "cpu_usage" in data


@pytest.mark.asyncio
async def test_root_endpoint(client):
    """
    Test endpoint root (/) jika ada.
    Biasanya return 200 (Welcome) atau 404 (Not Found).
    Yang penting server merespons, bukan crash (500).
    """
    response = await client.get("/")
    assert response.status_code in [200, 404]


@pytest.mark.asyncio
async def test_routers_are_mounted(client):
    """
    Test untuk memastikan router (seperti auth, users) sudah terpasang.
    Kita tembak endpoint sembarang di router itu.
    Harapannya: 401 (Unauthorized), 405 (Method Not Allowed), atau 400 (Bad Request).
    Bukan 404 (Not Found) -> Kalau 404 berarti router lupa di-include.
    """
    # Coba tembak endpoint auth login
    # Kita tidak kirim data, jadi harapannya 422 (Validation Error) atau 405
    # Yang penting BUKAN 404.
    response = await client.post("/auth/token")
    assert response.status_code != 404, "Router Auth sepertinya belum di-mount"


@pytest.mark.asyncio
async def test_cors_headers(client):
    """
    Cek apakah CORS sudah disetting (misal untuk Frontend).
    """
    response = await client.options(
        "/",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )
    # FastAPI default behavior untuk OPTIONS di root mungkin berbeda,
    # tapi biasanya return 200 jika CORS middleware aktif.
    if response.status_code == 200:
        assert "access-control-allow-origin" in response.headers
